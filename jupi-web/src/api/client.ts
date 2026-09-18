import type {
  HealthResponse,
  ChatResponse,
  Conversation,
  ConversationSummary,
  CreateConversationRequest,
  CreateConversationResponse,
  SendMessageRequest,
  SendMessageResponse,
  ApiError,
} from '../types/api';

const API_BASE = '/api/v1';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options?.headers ?? {}),
    },
    credentials: 'include',
    ...options,
  });

  if (!res.ok) {
    const errorBody: ApiError = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(errorBody.error ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export async function createConversation(
  body?: CreateConversationRequest,
): Promise<CreateConversationResponse> {
  return request<CreateConversationResponse>('/conversations', {
    method: 'POST',
    body: JSON.stringify(body ?? {}),
  });
}

export async function sendMessage(
  body: SendMessageRequest,
): Promise<SendMessageResponse> {
  return request<SendMessageResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function getConversation(
  conversationId: string,
): Promise<Conversation> {
  return request<Conversation>(`/conversations/${conversationId}`);
}

export async function listConversations(): Promise<ConversationSummary[]> {
  return request<{ conversations: ConversationSummary[] }>('/conversations').then(
    (data) => data.conversations,
  );
}