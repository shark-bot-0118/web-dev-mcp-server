# SAMPLE PAGE
MCPで生成したページを公開しています  
原則としてコードには何も手を加えていません  
本プロジェクトで実装しているMCPのwebアプリ構築ツール(create_website)で生成されたページをS3デプロイツール(deploy_to_s3)でアップロードした際に公開されたURLをそのまま載せています  
修正等は全く行なっておらず、実行結果そのままです  
※要するにMCPが指示を元に勝手にWebアプリを構築し、自動でS3にアップロードしWebページを公開しています  
インプットしたプロンプトは広範なWeb開発に対応したかったので様々なケースを意識しました  
※テストのためデザインの統一性や内容の一貫性が損なわれやすいように意図的に抽象的なプロンプトにしています

**注意**  
公開して1日程度で削除します  
一部詳細ページ("もっと見る"や製品詳細ページなど)などは生成していないので飛べない場合があります  
※サンプルなのでかなりザルな設定です...悪用はしないでね🥺

## PAGE URL
公開しているサンプルページのURLです  
URLと共に実施に使用したプロンプトも載せています

***<眼科のホームページ>***  

URL
```
http://website-62f814da-20250622171315.s3-website-ap-northeast-1.amazonaws.com/
```  
プロンプト
```
個人経営の眼科の病院のホームページを作成したい。ホームページには病院の紹介、病院の医療内容、病院の医療設備、病院の医療スタッフ、病院の医療価格、病院の医療予約、病院の医療連絡先を載せる。また、病院の医療内容には病院の医療内容を載せる。病院の医療設備には病院の医療設備を載せる。病院の医療スタッフには病院の医療スタッフを載せる。病院の医療価格には病院の医療価格を載せる。病院の医療予約には病院の医療予約を載せる。病院の医療連絡先には病院の医療連絡先を載せる。
```


***<中小企業のホームページ>***  

URL
```
http://website-37af87e1-20250622174611.s3-website-ap-northeast-1.amazonaws.com/
```
プロンプト
```
中小企業のホームページを作成したい。本企業はネジを主に生産しており、様々な大企業に対して販売している。ホームページでは会社の紹介を載せる。製品紹介ページでは様々な種類のネジを載せる。会社の紹介ページでは職人の名前と職人の有する貴重なスキルを紹介しこれまで受賞した様々な賞を掲載。会社の変遷ページにはこれまでの50年で会社が歩んできた歴史を紹介。コンタクトページには会社へのアクセスと製品に関する問い合わせ、製造依頼に関する受付先を掲載。
```

***<個人経営の蕎麦屋のホームページ>***

URL
```
http://website-2bf96243-20250622172946.s3-website-ap-northeast-1.amazonaws.com/
```
プロンプト
```
個人作家のホームページを作成したい。ホームページにはアトリエの紹介を載せ、アクセスした人が惹きつけられるような芸術的なイメージのページを作成してほしい。webページ全体として抽象的で動きのあるページにしてほしい。ホームページの他には作品の紹介ができるページと、紹介ページから販売ページに遷移するようにしてほしい。また、Youtubeチャンネルを持っているのでYoutubeチャンネルのリンクを載せるページも作成してください。追加でアトリエのイベントを載せるページとコンタクトページを作成してください。
```

***<サイバーパンク>***  
ローカルLLMにプロンプトは作成してもらいました

URL
```
http://website-daecd090-20250628135655.s3-website-ap-northeast-1.amazonaws.com/
```

プロンプト
"""
user_instruction: Create a 4-page portfolio website with a "Cyberpunk Glitch Art" theme. The site should have a dark background (#121212) with neon pink (#FF00FF), cyan (#00FFFF), and electric blue (#7DF9FF) accents. Use distorted typography (e.g., glitch font like 'Digital-7') and holographic textures throughout.

**Home Page:**
*   Hero Section: Animated intro sequence – a distorted logo reveal with a glitch effect, transitioning to the navigation menu. Navigation links should have subtle hover animations.
*   Featured Projects: Interactive grid layout where projects "glitch" into view on hover, revealing a short description and link.

**About Page:**
*   Animated timeline showcasing career progression using glitch effects for transitions between milestones. Each milestone should appear with a brief animation.
*   Skills/Expertise: Visual representation of skills with animated holographic icons that pulse gently.
*   Interactive "bio" section where text fragments appear and disappear in a glitchy pattern, triggered by mouse hover.

**Projects Page:**
*   Full project showcase – detailed descriptions, high-resolution images/videos for each project. Implement filtering options by category (e.g., graphic design, web development).
*   Each project should have a dedicated section with parallax scrolling effect when the user scrolls down.
*   Project thumbnails should animate on hover (e.g., zoom in slightly or display a short animation).

**Contact Page:**
*   Animated contact form with futuristic design elements – input fields should glow subtly and have animated borders.
*   Interactive map showing location (optional).
*   Social media links with animated icons that pulse gently.

The website should be responsive and look good on all devices. Prioritize clean code and optimized performance.
"""```

```

