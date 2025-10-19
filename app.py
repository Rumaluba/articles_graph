from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import time
from datetime import datetime, timedelta
import re
import urllib.parse

app = Flask(__name__)
CORS(app)

# Файл для хранения статей
ARTICLES_FILE = 'data/articles.json'

def load_articles():
    """Загружает статьи из файла"""
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'nodes': [], 'links': []}

def save_articles(articles_data):
    """Сохраняет статьи в файл"""
    os.makedirs('data', exist_ok=True)
    with open(ARTICLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, ensure_ascii=False, indent=2)

def ensure_url(article):
    """Гарантирует что у статьи есть URL"""
    if article.get('url'):
        return article['url']
    
    if article.get('doi'):
        return f"https://doi.org/{article['doi']}"
    elif 'pubmed_' in article.get('id', ''):
        pmid = article['id'].replace('pubmed_', '')
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    elif 'arxiv_' in article.get('id', ''):
        arxiv_id = article['id'].replace('arxiv_', '')
        return f"https://arxiv.org/abs/{arxiv_id}"
    elif article.get('source') == 'Crossref' and article.get('doi'):
        return f"https://doi.org/{article['doi']}"
    elif article.get('source') == 'Semantic Scholar' and article.get('id', '').startswith('semantic_'):
        paper_id = article['id'].replace('semantic_', '')
        return f"https://www.semanticscholar.org/paper/{paper_id}"
    
    title_encoded = urllib.parse.quote(article.get('title', ''))
    return f"https://scholar.google.com/scholar?q={title_encoded}"

def search_acs_publications(days_back=30):
    """Поиск в журналах American Chemical Society"""
    all_articles = []
    
    acs_journals = [
        "Macromolecules",
        "Biomacromolecules", 
        "Chemistry of Materials",
        "ACS Applied Materials & Interfaces",
        "ACS Macro Letters",
        "Journal of the American Chemical Society",
        "ACS Polymers Au",
        "Langmuir"
    ]
    
    for journal in acs_journals:
        print(f"Searching ACS Journal: {journal}")
        
        url = f"https://api.crossref.org/works?filter=container-title:{urllib.parse.quote(journal)}&rows=15&sort=published&order=desc"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            works = data.get('message', {}).get('items', [])
            print(f"Found {len(works)} articles from {journal}")
            
            for item in works:
                try:
                    title = item.get('title', ['No title'])[0]
                    abstract = item.get('abstract', 'No abstract available')
                    
                    published = item.get('created', {}).get('date-parts', [[None]])[0]
                    year = published[0] if published and published[0] else datetime.now().year
                    
                    doi = item.get('DOI', '')
                    
                    authors = []
                    for author in item.get('author', []):
                        given = author.get('given', '')
                        family = author.get('family', '')
                        if given or family:
                            authors.append(f"{given} {family}".strip())
                    
                    article_id = f"acs_{doi}" if doi else f"acs_{hash(title)}"
                    
                    article = {
                        'id': article_id,
                        'title': title,
                        'abstract': abstract[:500] + '...' if len(abstract) > 500 else abstract,
                        'full_abstract': abstract,
                        'year': year,
                        'journal': journal,
                        'keywords': ['ACS', 'chemistry', 'polymer', 'material science'],
                        'citation_count': max(item.get('is-referenced-by-count', 1), 1),
                        'doi': doi,
                        'published': str(year),
                        'search_keywords': [journal],
                        'authors': authors,
                        'source': 'ACS Publications',
                        'url': ''
                    }
                    
                    article['url'] = ensure_url(article)
                    
                    if not any(a['id'] == article['id'] for a in all_articles):
                        all_articles.append(article)
                        print(f"  - Added from {journal}: {article['title'][:50]}...")
                        
                except Exception as e:
                    print(f"Error processing ACS article: {e}")
                    continue
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error searching ACS journal {journal}: {e}")
            continue
    
    return all_articles

def search_rsc_publications(days_back=30):
    """Поиск в журналах Royal Society of Chemistry"""
    all_articles = []
    
    rsc_journals = [
        "Polymer Chemistry",
        "Journal of Materials Chemistry A",
        "Soft Matter",
        "Materials Horizons",
        "Green Chemistry"
    ]
    
    for journal in rsc_journals:
        print(f"Searching RSC Journal: {journal}")
        
        url = f"https://api.crossref.org/works?filter=container-title:{urllib.parse.quote(journal)}&rows=12&sort=published&order=desc"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            works = data.get('message', {}).get('items', [])
            print(f"Found {len(works)} articles from {journal}")
            
            for item in works:
                try:
                    title = item.get('title', ['No title'])[0]
                    abstract = item.get('abstract', 'No abstract available')
                    
                    published = item.get('created', {}).get('date-parts', [[None]])[0]
                    year = published[0] if published and published[0] else datetime.now().year
                    
                    doi = item.get('DOI', '')
                    
                    authors = []
                    for author in item.get('author', []):
                        given = author.get('given', '')
                        family = author.get('family', '')
                        if given or family:
                            authors.append(f"{given} {family}".strip())
                    
                    article_id = f"rsc_{doi}" if doi else f"rsc_{hash(title)}"
                    
                    article = {
                        'id': article_id,
                        'title': title,
                        'abstract': abstract[:500] + '...' if len(abstract) > 500 else abstract,
                        'full_abstract': abstract,
                        'year': year,
                        'journal': journal,
                        'keywords': ['RSC', 'chemistry', 'polymer', 'material science'],
                        'citation_count': max(item.get('is-referenced-by-count', 1), 1),
                        'doi': doi,
                        'published': str(year),
                        'search_keywords': [journal],
                        'authors': authors,
                        'source': 'RSC Publications',
                        'url': ''
                    }
                    
                    article['url'] = ensure_url(article)
                    
                    if not any(a['id'] == article['id'] for a in all_articles):
                        all_articles.append(article)
                        print(f"  - Added from {journal}: {article['title'][:50]}...")
                        
                except Exception as e:
                    print(f"Error processing RSC article: {e}")
                    continue
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error searching RSC journal {journal}: {e}")
            continue
    
    return all_articles

def search_springer_chemistry(days_back=30):
    """Поиск в Springer химических журналах"""
    all_articles = []
    
    springer_journals = [
        "Colloid and Polymer Science",
        "Journal of Polymer Research",
        "Polymer Bulletin",
        "Advances in Polymer Technology"
    ]
    
    chemistry_keywords = [
        "copolymer synthesis",
        "polymer characterization", 
        "barrier properties polymer",
        "polymer blend",
        "controlled polymerization",
        "polymer nanocomposite"
    ]
    
    for keyword in chemistry_keywords:
        print(f"Searching Springer for: {keyword}")
        
        url = f"https://api.crossref.org/works?query={urllib.parse.quote(keyword)}&rows=10&sort=relevance&order=desc"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            works = data.get('message', {}).get('items', [])
            print(f"Found {len(works)} articles for '{keyword}'")
            
            for item in works:
                try:
                    # Проверяем что это Springer статья
                    publisher = item.get('publisher', '').lower()
                    if 'springer' not in publisher:
                        continue
                        
                    title = item.get('title', ['No title'])[0]
                    abstract = item.get('abstract', 'No abstract available')
                    
                    published = item.get('created', {}).get('date-parts', [[None]])[0]
                    year = published[0] if published and published[0] else datetime.now().year
                    
                    journal = item.get('container-title', ['Springer Journal'])[0] if item.get('container-title') else 'Springer Journal'
                    doi = item.get('DOI', '')
                    
                    authors = []
                    for author in item.get('author', []):
                        given = author.get('given', '')
                        family = author.get('family', '')
                        if given or family:
                            authors.append(f"{given} {family}".strip())
                    
                    article_id = f"springer_{doi}" if doi else f"springer_{hash(title)}"
                    
                    article = {
                        'id': article_id,
                        'title': title,
                        'abstract': abstract[:500] + '...' if len(abstract) > 500 else abstract,
                        'full_abstract': abstract,
                        'year': year,
                        'journal': journal,
                        'keywords': [keyword, 'polymer', 'chemistry'],
                        'citation_count': max(item.get('is-referenced-by-count', 1), 1),
                        'doi': doi,
                        'published': str(year),
                        'search_keywords': [keyword],
                        'authors': authors,
                        'source': 'Springer',
                        'url': ''
                    }
                    
                    article['url'] = ensure_url(article)
                    
                    if not any(a['id'] == article['id'] for a in all_articles):
                        all_articles.append(article)
                        print(f"  - Added Springer: {article['title'][:50]}...")
                        
                except Exception as e:
                    print(f"Error processing Springer article: {e}")
                    continue
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error searching Springer for {keyword}: {e}")
            continue
    
    return all_articles

def search_wiley_polymers(days_back=30):
    """Поиск в Wiley полимерных журналах"""
    all_articles = []
    
    wiley_journals = [
        "Journal of Applied Polymer Science",
        "Journal of Polymer Science", 
        "Polymer International",
        "Macromolecular Rapid Communications"
    ]
    
    for journal in wiley_journals:
        print(f"Searching Wiley Journal: {journal}")
        
        url = f"https://api.crossref.org/works?filter=container-title:{urllib.parse.quote(journal)}&rows=12&sort=published&order=desc"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            works = data.get('message', {}).get('items', [])
            print(f"Found {len(works)} articles from {journal}")
            
            for item in works:
                try:
                    title = item.get('title', ['No title'])[0]
                    abstract = item.get('abstract', 'No abstract available')
                    
                    published = item.get('created', {}).get('date-parts', [[None]])[0]
                    year = published[0] if published and published[0] else datetime.now().year
                    
                    doi = item.get('DOI', '')
                    
                    authors = []
                    for author in item.get('author', []):
                        given = author.get('given', '')
                        family = author.get('family', '')
                        if given or family:
                            authors.append(f"{given} {family}".strip())
                    
                    article_id = f"wiley_{doi}" if doi else f"wiley_{hash(title)}"
                    
                    article = {
                        'id': article_id,
                        'title': title,
                        'abstract': abstract[:500] + '...' if len(abstract) > 500 else abstract,
                        'full_abstract': abstract,
                        'year': year,
                        'journal': journal,
                        'keywords': ['Wiley', 'polymer', 'applied science'],
                        'citation_count': max(item.get('is-referenced-by-count', 1), 1),
                        'doi': doi,
                        'published': str(year),
                        'search_keywords': [journal],
                        'authors': authors,
                        'source': 'Wiley',
                        'url': ''
                    }
                    
                    article['url'] = ensure_url(article)
                    
                    if not any(a['id'] == article['id'] for a in all_articles):
                        all_articles.append(article)
                        print(f"  - Added from {journal}: {article['title'][:50]}...")
                        
                except Exception as e:
                    print(f"Error processing Wiley article: {e}")
                    continue
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error searching Wiley journal {journal}: {e}")
            continue
    
    return all_articles

def search_semantic_scholar_advanced(days_back=30):
    """Расширенный поиск через Semantic Scholar"""
    all_articles = []
    
    advanced_queries = [
        "copolymer barrier properties mathematical model",
        "polymer diffusion simulation machine learning",
        "block copolymer self-assembly modeling",
        "polymer nanocomposite mechanical properties",
        "controlled radical polymerization kinetics"
    ]
    
    for query in advanced_queries:
        print(f"Searching Semantic Scholar for: {query}")
        
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query)}&limit=8&fields=title,abstract,url,year,venue,externalIds,citationCount,authors"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 429:
                print("Rate limit exceeded, waiting...")
                time.sleep(60)
                continue
                
            data = response.json()
            papers = data.get('data', [])
            print(f"Found {len(papers)} articles for '{query}'")
            
            for paper in papers:
                try:
                    title = paper.get('title', 'No title')
                    abstract = paper.get('abstract', 'No abstract available')
                    year = paper.get('year', datetime.now().year)
                    venue = paper.get('venue', 'Unknown')
                    citation_count = paper.get('citationCount', 0)
                    
                    authors = []
                    for author in paper.get('authors', []):
                        if author.get('name'):
                            authors.append(author['name'])
                    
                    article_id = f"semantic_adv_{paper.get('paperId', hash(title))}"
                    
                    article = {
                        'id': article_id,
                        'title': title,
                        'abstract': abstract[:500] + '...' if len(abstract) > 500 else abstract,
                        'full_abstract': abstract,
                        'year': year,
                        'journal': venue,
                        'keywords': [query],
                        'citation_count': max(citation_count, 1),
                        'doi': paper.get('externalIds', {}).get('DOI', ''),
                        'published': str(year),
                        'search_keywords': [query],
                        'authors': authors,
                        'source': 'Semantic Scholar',
                        'url': paper.get('url', '')
                    }
                    
                    article['url'] = ensure_url(article)
                    
                    if not any(a['id'] == article['id'] for a in all_articles):
                        all_articles.append(article)
                        print(f"  - Added: {article['title'][:50]}... (Citations: {citation_count})")
                        
                except Exception as e:
                    print(f"Error processing Semantic Scholar paper: {e}")
                    continue
            
            time.sleep(2)
            
        except Exception as e:
            print(f"Error searching Semantic Scholar for {query}: {e}")
            continue
    
    return all_articles

def search_pubmed_articles(days_back=30):
    """Поиск статей в PubMed"""
    all_articles = []
    
    search_queries = [
        "copolymer AND barrier AND properties",
        "block copolymer AND self-assembly",
        "polymer AND nanocomposite AND modeling"
    ]
    
    for query in search_queries:
        print(f"Searching PubMed for: {query}")
        
        # Используем Crossref как fallback для PubMed-like статей
        url = f"https://api.crossref.org/works?query={urllib.parse.quote(query)}&rows=8&sort=relevance&order=desc"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            
            works = data.get('message', {}).get('items', [])
            print(f"Found {len(works)} articles for '{query}'")
            
            for item in works:
                try:
                    title = item.get('title', ['No title'])[0]
                    abstract = item.get('abstract', 'No abstract available')
                    
                    published = item.get('created', {}).get('date-parts', [[None]])[0]
                    year = published[0] if published and published[0] else datetime.now().year
                    
                    doi = item.get('DOI', '')
                    journal = item.get('container-title', ['PubMed-like Journal'])[0] if item.get('container-title') else 'PubMed-like Journal'
                    
                    authors = []
                    for author in item.get('author', []):
                        given = author.get('given', '')
                        family = author.get('family', '')
                        if given or family:
                            authors.append(f"{given} {family}".strip())
                    
                    if not authors:
                        authors = ['Authors not specified']
                    
                    article_id = f"pubmed_like_{doi}" if doi else f"pubmed_like_{hash(title)}"
                    
                    article = {
                        'id': article_id,
                        'title': title,
                        'abstract': abstract[:500] + '...' if len(abstract) > 500 else abstract,
                        'full_abstract': abstract,
                        'year': year,
                        'journal': journal,
                        'keywords': query.split(' AND '),
                        'citation_count': max(item.get('is-referenced-by-count', 1), 1),
                        'doi': doi,
                        'published': str(year),
                        'search_keywords': [query],
                        'authors': authors,
                        'source': 'PubMed-like',
                        'url': f"https://doi.org/{doi}" if doi else f"https://scholar.google.com/scholar?q={urllib.parse.quote(title)}"
                    }
                    
                    all_articles.append(article)
                    print(f"  - Added PubMed-like: {title[:50]}...")
                    
                except Exception as e:
                    print(f"Error processing PubMed-like article: {e}")
                    continue
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error searching PubMed-like for {query}: {e}")
            continue
    
    return all_articles

def search_articles(start_date, end_date):
    """Объединяет поиск из всех источников"""
    all_articles = []
    
    print(f"Starting comprehensive article search from {start_date} to {end_date}...")
    
    print("1. Searching ACS Publications...")
    acs_articles = search_acs_publications()
    all_articles.extend(acs_articles)
    
    print("2. Searching RSC Publications...")
    rsc_articles = search_rsc_publications()
    all_articles.extend(rsc_articles)
    
    print("3. Searching Springer...")
    springer_articles = search_springer_chemistry()
    all_articles.extend(springer_articles)
    
    print("4. Searching Wiley...")
    wiley_articles = search_wiley_polymers()
    all_articles.extend(wiley_articles)
    
    print("5. Searching Semantic Scholar...")
    semantic_articles = search_semantic_scholar_advanced()
    all_articles.extend(semantic_articles)
    
    print("6. Searching PubMed-like sources...")
    pubmed_articles = search_pubmed_articles()
    all_articles.extend(pubmed_articles)
    
    # Удаляем дубликаты по ID
    unique_articles = {}
    for article in all_articles:
        if article['id'] not in unique_articles:
            unique_articles[article['id']] = article
    
    all_articles = list(unique_articles.values())
    
    print(f"Total unique articles found: {len(all_articles)}")
    return all_articles

def build_citation_network(articles):
    """Строит сеть цитирований и связей по авторам"""
    nodes = []
    links = []
    
    # Создаем узлы
    for article in articles:
        article['url'] = ensure_url(article)
        nodes.append({
            'id': article['id'],
            'title': article['title'],
            'abstract': article['abstract'],
            'full_abstract': article.get('full_abstract', article['abstract']),
            'year': article['year'],
            'journal': article['journal'],
            'keywords': article['keywords'],
            'citation_count': article['citation_count'],
            'search_keywords': article.get('search_keywords', []),
            'authors': article.get('authors', []),
            'source': article.get('source', 'Unknown'),
            'url': article['url']
        })
    
    # Создаем связи
    for i, article1 in enumerate(articles):
        for j, article2 in enumerate(articles):
            if i >= j:  # Избегаем дублирования
                continue
                
            # Связь по авторам
            authors1 = set(author.lower().strip() for author in article1.get('authors', []))
            authors2 = set(author.lower().strip() for author in article2.get('authors', []))
            common_authors = authors1.intersection(authors2)
            
            if common_authors:
                links.append({
                    'source': article1['id'],
                    'target': article2['id'],
                    'strength': len(common_authors) * 2,
                    'type': 'authors',
                    'common_authors': list(common_authors)
                })
            
            # Связь по ключевым словам
            keywords1 = set(kw.lower() for kw in article1['keywords'] + article1.get('search_keywords', []))
            keywords2 = set(kw.lower() for kw in article2['keywords'] + article2.get('search_keywords', []))
            common_keywords = keywords1.intersection(keywords2)
            
            if common_keywords:
                links.append({
                    'source': article1['id'],
                    'target': article2['id'],
                    'strength': len(common_keywords),
                    'type': 'keywords',
                    'common_keywords': list(common_keywords)
                })
    
    return {'nodes': nodes, 'links': links}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/articles')
def get_articles():
    """API endpoint для получения статей с фильтрами"""
    topic = request.args.get('topic', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    articles_data = load_articles()
    nodes = articles_data.get('nodes', [])
    links = articles_data.get('links', [])
    
    print(f"Loaded {len(nodes)} nodes, {len(links)} links")
    
    if topic != 'all':
        topic_map = {
            'copolymer': ['copolymer', 'polymer', 'blend', 'macromolecule'],
            'barrier': ['barrier', 'permeability', 'gas', 'diffusion'], 
            'model': ['model', 'learning', 'neural', 'simulation', 'mathematical']
        }
        if topic in topic_map:
            search_terms = topic_map[topic]
            filtered_nodes = []
            for node in nodes:
                node_text = ' '.join([
                    ' '.join(node.get('search_keywords', [])),
                    ' '.join(node.get('keywords', [])),
                    node.get('title', ''),
                    node.get('abstract', '')
                ]).lower()
                
                if any(term in node_text for term in search_terms):
                    filtered_nodes.append(node)
            nodes = filtered_nodes
    
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            nodes = [node for node in nodes if node['year'] >= start_date_obj.year]
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            nodes = [node for node in nodes if node['year'] <= end_date_obj.year]
        except ValueError:
            pass
    
    node_ids = {node['id'] for node in nodes}
    filtered_links = [
        link for link in links 
        if link['source'] in node_ids and link['target'] in node_ids
    ]
    
    return jsonify({'nodes': nodes, 'links': filtered_links})

@app.route('/api/update-articles')
def update_articles():
    """Ручное обновление статей"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'status': 'error', 'message': 'Start date and end date are required'})
        
        print(f"Starting articles update from {start_date} to {end_date}...")
        
        new_articles = search_articles(start_date, end_date)
        existing_data = load_articles()
        existing_articles = existing_data.get('nodes', [])
        
        all_articles = existing_articles.copy()
        existing_ids = {article['id'] for article in existing_articles}
        
        actually_new = []
        for new_article in new_articles:
            if new_article['id'] not in existing_ids:
                all_articles.append(new_article)
                actually_new.append(new_article)
        
        graph_data = build_citation_network(all_articles)
        save_articles(graph_data)
        
        sources = list(set(a["source"] for a in actually_new))
        
        return jsonify({
            'status': 'success', 
            'message': f'Added {len(actually_new)} new articles from {start_date} to {end_date}',
            'total_articles': len(all_articles),
            'sources': sources
        })
        
    except Exception as e:
        print(f"Error in update_articles: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
