


import dakarta

from decouple import  config
from fastapi import FastAPI, Query

from tasks import run_scraper_neigeria, celery_app
from utils_neigeria import all_pages_looping as neigeria_scraper

# setting proxy config

proxy_host = config("PROXY_HOST")
proxy_port = config("PROXY_PORT")
proxy_user = config("proxy_user")
proxy_pass = config("proxy_pass")
proxy_string = f"{proxy_host}:{proxy_port}"  #cc-us-city-new_york-sessid-test123.bc.pr.oxylabs.io:7777# Add proxy
# Add proxy authentication via extension


app = FastAPI()

#url = "https://nigeriapropertycentre.com/for-rent/flats-apartments/lagos?q=for-rent+flats-apartments+lagos&"

app.include_router(dakarta.router)
@app.get("/neigeria")
def scrape(
    url: str = Query(..., description="Listing URL to scrape"),
    max_page: int = Query(1, description="Maximum number of pages to scrape")  #  default = 25
):

    """
    Call:  GET /neigeria?url=https://nigeriapropertycentre.com/for-rent/flats-apartments/lagos?q=for-rent+flats-apartments+lagos&
    """
    task = run_scraper_neigeria.delay(url, max_page)
    return {"task_id": task.id, "status": "queued"}

    #return neigeria_scraper(url, max_page)

@app.get("/status/neigeria/{task_id}")
def get_neigeria_status(task_id: str):
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.successful() else None,
    }













