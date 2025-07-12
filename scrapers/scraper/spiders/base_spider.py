import scrapy


class BaseDetailSpider(scrapy.Spider):
  """
    Base class for any spider that needs stub-page detection + retry.
    Subclasses must override:
      `is_stub(response) -> bool`


    """

  def is_stub(response)->bool:
    """
      Return True if this response is a stub page and should be retried.
     """
    return NotImplementedError("Detail spiders must override is_stub()->bool")
