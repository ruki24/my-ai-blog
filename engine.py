import os
import datetime
import google.generativeai as genai

# --- Configuration ---
# APIキー設定（main内で実行）
API_KEY = None

TEMPLATE_PATH = "template.html"
OUTPUT_DIR = "posts"

def fetch_trending_topics():
    """
    現在はサンプルのトレンドを返します。
    将来的に Google Trends API や RSS フィードから取得するように拡張可能です。
    """
    return [
        {"title": "2026年のAIエージェントの進化", "category": "Technology"},
        {"title": "リモートワークを最適化するデスクトップ環境", "category": "Lifestyle"},
        {"title": "次世代のWebデザイン：グラスモーフィズムの再来", "category": "Design"}
    ]

def generate_article(topic):
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = f"""
    以下のトピックについて、SEOに最適化された高品質なブログ記事を日本語で執筆してください。
    トピック: {topic['title']}
    カテゴリ: {topic['category']}
    
    構成ルール:
    - 読者の興味を引く導入文
    - 適切な見出し（## 見出し）の使用
    - 具体的なメリットや実例を含める
    - 【重要】後半には、トピックに関連する「役立つ道具や本」を3つ紹介するセクションを含めてください。
    - 各商品は「商品名」「選定理由」「[Amazonで検索](https://www.amazon.co.jp/s?k=商品名)」の形式で記載してください。
    
    出力形式:
    以下の項目を含むJSON形式で出力してください。
    - "title": 記事のタイトル
    - "content": 記事の本文（GitHub Pages用のマークダウン）
    - "note_draft": note.comのエディタに最適化されたプレーンテキスト形式の下書き
    - "slug": URL用スラッグ（例: ai-evolution-2026）
    - "image_prompt": この記事の内容を表す、AI画像生成用の英語プロンプト（短い一文）
    """
    
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    import json
    return json.loads(response.text)

def download_image(prompt, save_path):
    import requests
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=512&seed=42&model=flux"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Image download failed: {e}")
    return False

def save_as_html(topic, article_data):
    import markdown
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    
    # スラッグをファイル名に使用
    slug = article_data.get('slug', 'article').lower().replace(' ', '-')
    date_str = datetime.date.today().strftime('%Y%m%d')
    
    # 画像の生成と保存
    image_filename = f"{date_str}_{slug}.jpg"
    image_filepath = os.path.join(OUTPUT_DIR, image_filename)
    header_image_url = f"posts/{image_filename}"
    
    print(f"Generating image for: {article_data.get('image_prompt')}")
    if not download_image(article_data.get('image_prompt', 'Future technology'), image_filepath):
        # 失敗時はプレースホルダー
        header_image_url = "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&q=80&w=1024&h=512"

    # マークダウンをHTMLに変換
    html_content = markdown.markdown(article_data['content'])
    
    # テンプレート置換
    html = template.replace("{{ title }}", article_data['title'])
    html = html.replace("{{ category }}", topic['category'])
    html = html.replace("{{ date }}", datetime.date.today().strftime("%Y-%m-%d"))
    html = html.replace("{{ content }}", html_content)
    html = html.replace("{{ header_image }}", header_image_url)
    
    filename = f"{date_str}_{slug}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    # note用の下書き保存
    note_filename = f"{date_str}_{slug}_note.txt"
    note_filepath = os.path.join(OUTPUT_DIR, note_filename)
    with open(note_filepath, "w", encoding="utf-8") as f:
        f.write(f"タイトル: {article_data['title']}\n\n")
        f.write(f"画像プロンプト: {article_data.get('image_prompt', '')}\n\n")
        f.write(article_data['note_draft'])
    
    print(f"Generated HTML: {filepath}")
    print(f"Generated Note Draft: {note_filepath}")
    update_index(topic, article_data, filepath, header_image_url)

def update_index(topic, article_data, filepath, header_image_url):
    INDEX_PATH = "index.html"
    rel_path = os.path.relpath(filepath, ".")
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # パス区切り文字を統一
    link_url = rel_path.replace("\\", "/")
    img_url = header_image_url.replace("\\", "/")
    
    new_entry = f"""
            <div class="glass p-6 transition hover:scale-[1.02] flex flex-col md:flex-row gap-6">
                <div class="md:w-1/3 h-48 rounded-xl overflow-hidden shadow-inner">
                    <img src="{img_url}" alt="thumbnail" class="w-full h-full object-cover">
                </div>
                <div class="md:w-2/3">
                    <a href="{link_url}" class="block h-full">
                        <span class="text-xs text-indigo-400 font-bold uppercase">{topic['category']}</span>
                        <h2 class="text-2xl font-bold mt-2">{article_data['title']}</h2>
                        <p class="text-slate-400 text-sm mt-2">{date_str}</p>
                    </a>
                </div>
            </div>
    """
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 重複チェック（タイトルまたは同じリンクが既にある場合はスキップ）
        if f'href="{link_url}"' in content or article_data['title'] in content:
            print(f"Skipping index update: Article '{article_data['title']}' already exists.")
            return

        if "<!-- 記事リストがここに追加されます -->" in content:
            content = content.replace("<!-- 記事リストがここに追加されます -->", f"<!-- 記事リストがここに追加されます -->\n{new_entry}")
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                f.write(content)
            print("Index updated.")

def main():
    print("Starting AI Blog Engine...")
    
    # 環境変数の詳細チェック
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY が設定されていません。GitHub Secrets を確認してください。")
        exit(1)
        
    try:
        genai.configure(api_key=api_key)
        topics = fetch_trending_topics()
        
        # 最初のトピックを使用
        topic = topics[0]
        print(f"Generating content for: {topic['title']}")
        
        article_data = generate_article(topic)
        save_as_html(topic, article_data)
        print("Success!")
    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
