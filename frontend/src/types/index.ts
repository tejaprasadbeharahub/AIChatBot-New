export type ChatHistoryItem = {
	role: 'user' | 'assistant'
	content: string
}

export type ChatApiResponse = {
	reply: string
	model: string
}
