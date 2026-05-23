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
    - 純粋なマークダウンテキストで出力してください。
    """
    
    response = model.generate_content(prompt)
    return response.text

def save_as_html(topic, content):
    import markdown
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    
    # マークダウンをHTMLに変換
    html_content = markdown.markdown(content)
    
    # テンプレート置換
    html = template.replace("{{ title }}", topic['title'])
    html = html.replace("{{ category }}", topic['category'])
    html = html.replace("{{ date }}", datetime.date.today().strftime("%Y-%m-%d"))
    html = html.replace("{{ content }}", html_content)
    
    filename = f"{datetime.date.today().strftime('%Y%m%d')}_{topic['title'].replace(' ', '_')}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Generated: {filepath}")
    update_index(topic, filepath)

def update_index(topic, filepath):
    INDEX_PATH = "index.html"
    rel_path = os.path.relpath(filepath, ".")
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    
    new_entry = f"""
            <div class="glass p-6 transition hover:scale-[1.02]">
                <a href="{rel_path.replace("\\", "/")}" class="block">
                    <span class="text-xs text-indigo-400 font-bold uppercase">{topic['category']}</span>
                    <h2 class="text-2xl font-bold mt-2">{topic['title']}</h2>
                    <p class="text-slate-400 text-sm mt-2">{date_str}</p>
                </a>
            </div>
    """
    
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
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
        
        # テストとして最初の1つだけ実行
        topic = topics[0]
        print(f"Generating content for: {topic['title']}")
        
        content = generate_article(topic)
        save_as_html(topic, content)
        print("Success!")
    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1) # ワークフローを失敗させるために 1 を返す

if __name__ == "__main__":
    main()
