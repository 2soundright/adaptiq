# Multilingual Support

## Language Support

AdaptIQ supports three languages throughout the user experience:

| Language | Code | Coverage |
|----------|------|----------|
| English | en | Full support — default language |
| Russian | ru | Full support — auto-detected from Cyrillic text |
| Kazakh | kk | Full support — auto-detected |

### How It Works
- **Automatic detection**: The system detects the language of each query using the `langdetect` library
- **Response matching**: The AI is instructed to respond in the same language as the question
- **Safety messages**: Block messages for unsafe queries are localized in all three languages
- **No-docs messages**: When no relevant documents are found, the fallback message appears in the detected language
- **Query expansion**: The query transformation step preserves the original language
