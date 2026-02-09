# Fashion Chatbot Test Queries

## ✅ Valid Fashion Queries (Should Get Responses)

### English
- What are the latest fashion trends for 2024?
- How do I style a black dress for a party?
- What makeup looks good with a red dress?
- Can you suggest accessories for a casual outfit?
- What's the best skincare routine for dry skin?
- How to choose the right hairstyle for my face shape?
- What are sustainable fashion brands?
- How do I dress for a job interview?
- What colors go well together in an outfit?
- Tips for winter fashion?

### Spanish
- ¿Cuáles son las últimas tendencias de moda?
- ¿Cómo puedo combinar un vestido negro?
- ¿Qué maquillaje me recomiendas para una boda?
- Consejos de moda para el verano

### French
- Quelles sont les tendances mode actuelles?
- Comment porter une veste en jean?
- Quel maquillage pour les yeux verts?
- Conseils de style pour l'automne

### German
- Was sind die neuesten Modetrends?
- Wie style ich ein weißes Hemd?
- Welche Frisur passt zu mir?
- Tipps für Business-Mode

### Italian
- Quali sono le ultime tendenze della moda?
- Come abbinare i colori nell'abbigliamento?
- Consigli di trucco per principianti

### Portuguese
- Quais são as tendências de moda atuais?
- Como usar jeans rasgado?
- Dicas de maquiagem para pele oleosa

### Hindi
- फैशन के नए ट्रेंड क्या हैं?
- साड़ी कैसे पहनें?
- मेकअप टिप्स बताइए

### Arabic
- ما هي أحدث صيحات الموضة؟
- كيف أنسق ملابسي؟
- نصائح للعناية بالبشرة

### Japanese
- 最新のファッショントレンドは何ですか？
- 黒いドレスの着こなし方は？
- メイクのコツを教えてください

### Chinese
- 最新的时尚趋势是什么？
- 如何搭配衣服？
- 化妆技巧有哪些？

### Korean
- 최신 패션 트렌드는 무엇인가요?
- 검은색 드레스 스타일링 방법은?
- 메이크업 팁 알려주세요

## ❌ Out-of-Scope Queries (Should Be Declined)

### General Knowledge
- What is the capital of France?
- How does photosynthesis work?
- Who won the World Cup in 2022?
- What's the weather today?

### Technology
- How do I code in Python?
- What's the best smartphone to buy?
- How to fix my computer?
- Explain artificial intelligence

### Food & Cooking
- What's a good recipe for pasta?
- How to bake a cake?
- Best restaurants in New York
- Healthy meal plans

### Health & Medicine
- What medicine should I take for a headache?
- How to treat a cold?
- Symptoms of diabetes
- Best exercises to lose weight

### Finance
- How to invest in stocks?
- What's the exchange rate?
- Best credit cards
- How to save money?

### Travel
- Best places to visit in Europe
- How to book a flight?
- Travel tips for Japan
- Cheapest hotels in Paris

## 🔀 Edge Cases & Mixed Queries

### Borderline Fashion-Related (Should Accept)
- What shoes are comfortable for walking?
- How to remove makeup stains from clothes?
- Best fabrics for summer clothing
- How to organize my wardrobe?
- What to wear to a wedding?

### Mixed Topics (Should Decline)
- What's the best fashion app and how to code it?
- Fashion trends and stock market analysis
- Can you cook pasta and suggest an outfit?

## 🧪 Special Test Cases

### Empty/Invalid Input
- (empty message)
- ...
- ???
- 123456

### Very Short Queries
- Fashion?
- Makeup
- Style
- Trends

### Very Long Queries
- I'm going to a wedding next month and I have no idea what to wear. It's going to be outdoors in the summer and the dress code is semi-formal. I have a blue dress but I'm not sure if it's appropriate. Can you help me with outfit suggestions, accessories, shoes, and makeup ideas that would work well for this occasion?

### Multiple Languages in One Query
- What are fashion trends? ¿Cuáles son las tendencias?
- Fashion tips और मेकअप सलाह

## 📊 Testing Checklist

- [ ] All 11 languages are detected correctly
- [ ] Fashion queries get relevant responses
- [ ] Non-fashion queries are politely declined
- [ ] Out-of-scope messages are in the correct language
- [ ] Empty messages are handled gracefully
- [ ] Very long messages work properly
- [ ] Special characters don't break the bot
- [ ] Response time is acceptable (<2 seconds)
- [ ] UI displays all languages correctly
- [ ] Mobile responsiveness works

## 🎯 Quick Test Script

Copy and paste these one by one:

1. `What are the latest fashion trends?`
2. `¿Cómo combinar un vestido negro?`
3. `What is the capital of France?`
4. `Comment porter une veste en jean?`
5. `How to code in Python?`
6. `最新のファッショントレンドは何ですか？`
7. `Best restaurants in New York`
8. `Tips for winter fashion?`
9. `ما هي أحدث صيحات الموضة؟`
10. `How to invest in stocks?`
