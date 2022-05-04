from numpy import tile
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from lxml import html
from neomodel import StructuredNode, StringProperty, RelationshipTo, RelationshipFrom, config

config.DATABASE_URL = 'bolt://neo4j:19882001@localhost:7687'

class Book(StructuredNode):
    title = StringProperty()
    med = StringProperty()
    ISBN13 = StringProperty(unique_index=True)
    ISBN10 = StringProperty()
    link = StringProperty()
    image = StringProperty()
    year = StringProperty()
    author = RelationshipTo('Author', 'AUTHOR')

class Author(StructuredNode):
    link = StringProperty(unique_index=True)
    name = StringProperty()
    books = RelationshipFrom('Book', 'AUTHOR')

class AuthorsWorksSpider(CrawlSpider):
    name = 'authors_works'
    allowed_domains = ['books-by-isbn.com']
    start_urls = ['https://www.books-by-isbn.com/']
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
    rules = [
        Rule(
            LinkExtractor(
                unique=True
            ),
            follow=True,
            callback="parse_books"
        )
    ]

    def parse_books(self, response):
        if response.css('.title::text').get() is not None:

            book = {
                'title': response.css('.title::text').get(), 
                'med': response.css('.med::text').get(), 
                'ISBN13': response.css('.i13::text').get(), 
                'ISBN10': response.css('.i10::text').get(),
                'image': response.css('img.cover::attr(src)').get(),
                'year':response.css('.pubinf::text').get(),
                'link': response.url
                }


            authors = [{'link':x[0], 'name': x[1]} for x in list(zip(response.css('.auts a').xpath('@href').extract(), response.css('.auts a::text').extract()))]
 
            db_book = Book(
                title=book['title'],
                med = book['med'],
                ISBN13 = book['ISBN13'],
                ISBN10 = book['ISBN10'],
                link = book['link'],
                image = book['image'],
                year = book['year']
            ).save()
            
            for author in authors:
                db_author = Author.get_or_create(author)[0]
                db_book.author.connect(db_author)

            yield book
        else:
            print('not a book')