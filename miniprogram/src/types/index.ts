export interface Book {
  id: string
  title: string
  author: string
  sentence_count: number
  sort_order: number
}

export interface RelatedQuote {
  text: string
  book_title: string
  book_author: string
  sentence_id?: string
  book_found?: boolean
  author_multi_book?: boolean
}

export interface Sentence {
  id: string
  book_id: string
  text: string
  context_before: string
  context_after: string
  chapter: string
  ai_explanation: string
  counter_quote: string
  counter_source: string
  similar_quotes: RelatedQuote[]
  opposite_quotes: RelatedQuote[]
  sort_order: number
  is_bookmarked: boolean
}

export interface BookWithSentences {
  book: Book
  sentences: Sentence[]
}

export interface BookmarkItem {
  id: string
  sentence_id: string
  text: string
  context_before: string
  context_after: string
  book_title: string
  book_author: string
  chapter: string
  similar_quotes: RelatedQuote[]
  opposite_quotes: RelatedQuote[]
  created_at: string
}
