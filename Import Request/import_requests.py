import os
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime
import aiohttp
import asyncio

#TODO: Hostování skriptu na GitHub a spuštění skriptu každý týden pomocí GitHub Actions
#TODO: Ukládání na Google Drive pomocí Google Drive API
#TODO: Vylepšení skriptu aby mohl stahovat data z jiných zdrojů než jobs.cz
#DONE: Vylepšení skriptu použitím async funkce pro rychlejší asynchronní stahování dat


base_url = "https://www.jobs.cz/prace/?q%5B%5D=python&page="
pages = 4  #  počet stránek, které chceš procházet

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Vytvoření PDF souboru
pdf_filename = os.path.dirname(__file__) + "/results/" + f"job_listings_python_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf"
if not os.path.exists(os.path.dirname(pdf_filename)):
    os.makedirs(os.path.dirname(pdf_filename))
doc = SimpleDocTemplate(pdf_filename, pagesize=letter, leftMargin=20, rightMargin=20, topMargin=30, bottomMargin=30)
elements = []

# Register DejaVuSans font for UTF-8 support
font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')
pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='CustomStyle',
    fontName='DejaVuSans',
    fontSize=10,
    encoding='UTF-8'
))

async def fetch(session, url):
    print(f"Fetching URL: {url}")
    async with session.get(url, headers=headers) as response:
        return await response.text()

async def fetch_job_details(session, job_url):
    print(f"Fetching job details from URL: {job_url}")
    job_response_text = await fetch(session, job_url)
    job_soup = BeautifulSoup(job_response_text, 'html.parser')
    job_detail_title = job_soup.find('h1', class_='typography-heading-medium-text')
    job_detail_title = job_detail_title.get_text(strip=True) if job_detail_title else "N/A"
    company = job_soup.find('p', class_='typography-body-medium-text-regular')
    company = company.get_text(strip=True) if company else "N/A"
    location = job_soup.find('a', class_='link-secondary link-underlined')
    location = location.get_text(strip=True) if location else "N/A"
    description = job_soup.find('div', class_='RichContent mb-1400')
    description = description.get_text(strip=True) if description else "N/A"
    return job_detail_title, company, location, description

async def main():
    print("Starting the scraping process...")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for page in range(1, pages + 1):
            url = f"{base_url}{page}"
            tasks.append(fetch(session, url))
        pages_content = await asyncio.gather(*tasks)

        job_tasks = []
        for page_content in pages_content:
            soup = BeautifulSoup(page_content, 'html.parser')
            job_links = soup.find_all('a', class_='link-primary SearchResultCard__titleLink')
            for job in job_links:
                job_url = job['href']
                job_tasks.append(fetch_job_details(session, job_url))

        job_details = await asyncio.gather(*job_tasks)
        for job_detail_title, company, location, description in job_details:
            elements.append(Paragraph(f"Název pozice: {job_detail_title}", styles['CustomStyle']))
            elements.append(Paragraph(f"Společnost: {company}", styles['CustomStyle']))
            elements.append(Paragraph(f"Lokalita: {location}", styles['CustomStyle']))
            elements.append(Paragraph(f"Popis:", styles['CustomStyle']))
            elements.append(Paragraph(f"{description}", styles['CustomStyle']))
            elements.append(Spacer(1, 12))

    doc.build(elements)
    print(f"Data byla úspěšně uložena do souboru {pdf_filename}")

if __name__ == "__main__":
    asyncio.run(main())
    print("Scraping process completed.")