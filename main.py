import asyncio
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from urllib.parse import urljoin, urlparse

async def extract_links(html, base_url):
    """Extracts relevant subpage links from the given HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        full_url = urljoin(base_url, href)  # Convert to absolute URL

        # Filter out external links, keeping only links within the same domain
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url)

    return list(links)

async def auto_crawl_website(start_url):
    config = CrawlerRunConfig(markdown_generator=DefaultMarkdownGenerator())

    async with AsyncWebCrawler(verbose=True) as crawler:
        session_id = "dynamic_crawl_session"
        all_markdown = []  # Store extracted Markdown content
        visited_urls = set()  # To prevent re-crawling the same links
        queue = [start_url]  # Start with the base URL

        while queue:
            current_url = queue.pop(0)
            if current_url in visited_urls:
                continue

            print(f"\n🔍 Crawling: {current_url}\n")
            visited_urls.add(current_url)

            # Crawl the page only once
            result = await crawler.arun(
                url=current_url,
                session_id=session_id,
                config=config,
                bypass_cache=True,
            )

            assert result.success, f"❌ Failed to crawl {current_url}"

            markdown_content = result.markdown.strip() if result.markdown else ""
            if markdown_content:
                all_markdown.append(f"\n## {current_url}\n" + markdown_content)
            else:
                print(f"⚠ Warning: No Markdown extracted for {current_url}")

            # Extract new links dynamically
            new_links = await extract_links(result.html, current_url)
            for link in new_links:
                if link not in visited_urls and link.startswith(start_url):
                    queue.append(link)  

        print(f"\n✅ Successfully crawled {len(visited_urls)} unique pages from {start_url}")

        output_filename = "output1.txt"
        if all_markdown:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.writelines(all_markdown)
            print(f"✅ Full Markdown saved to {output_filename}")
        else:
            print(f"⚠ No Markdown content extracted. {output_filename} was not created.")

asyncio.run(auto_crawl_website("https://en.wikipedia.org/wiki/Harry_Potter"))
