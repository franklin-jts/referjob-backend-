import AsyncStorage from '@react-native-async-storage/async-storage';

// ── Change this to your PC's IP when testing on a real device ─────────────────
export const BASE_URL = 'http://192.168.29.118:8000';

// ── Token helpers ─────────────────────────────────────────────────────────────
export const saveToken = (token: string) => AsyncStorage.setItem('token', token);
export const getToken  = ()              => AsyncStorage.getItem('token');
export const removeToken = ()            => AsyncStorage.removeItem('token');

export const saveUser = (user: any)      => AsyncStorage.setItem('user', JSON.stringify(user));
export const getUser  = async ()         => {
  const u = await AsyncStorage.getItem('user');
  return u ? JSON.parse(u) : null;
};
export const removeUser = ()             => AsyncStorage.removeItem('user');

// ── Base fetch wrapper ────────────────────────────────────────────────────────
async function request(path: string, options: RequestInit = {}) {
  const token = await getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  const data = await res.json();
  if (!res.ok) {
    // FastAPI returns { detail: "..." } on errors
    throw new Error(data.detail || 'Something went wrong');
  }
  return data;
}

// ── Auth API ──────────────────────────────────────────────────────────────────
export const authAPI = {

  // POST /api/auth/register
  register: (body: {
    name: string;
    email: string;
    password: string;
    username?: string;
    mobile?: string;
    title?: string;
    company?: string;
    location?: string;
    bio?: string;
    skills?: string[];
    avatar?: string;
  }) => request('/api/auth/register', { method: 'POST', body: JSON.stringify(body) }),

  // POST /api/auth/login
  // Sends: email (accepts email OR mobile), password
  login: (email: string, password: string) =>
    request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  // GET /api/auth/me  — validate token, get current user
  me: () => request('/api/auth/me'),

  // POST /api/auth/suggest-username
  suggestUsername: (first_name: string, last_name: string) =>
    request('/api/auth/suggest-username', {
      method: 'POST',
      body: JSON.stringify({ first_name, last_name }),
    }),

  // GET /api/auth/check-username/:username
  checkUsername: (username: string) =>
    request(`/api/auth/check-username/${username}`),

  // POST /api/auth/forgot-password
  // Sends: identifier (email OR mobile)
  forgotPassword: (identifier: string) =>
    request('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ identifier }),
    }),

  // POST /api/auth/reset-password
  resetPassword: (reset_token: string, new_password: string, confirm_password: string) =>
    request('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ reset_token, new_password, confirm_password }),
    }),
};

// ── Posts API ─────────────────────────────────────────────────────────────────
export const postsAPI = {
  getFeed:    (skip = 0, limit = 20) => request(`/api/posts/?skip=${skip}&limit=${limit}`),
  getPost:    (id: string)           => request(`/api/posts/${id}`),
  createPost: (body: any)            => request('/api/posts/', { method: 'POST', body: JSON.stringify(body) }),
  deletePost: (id: string)           => request(`/api/posts/${id}`, { method: 'DELETE' }),
  likePost:   (id: string)           => request(`/api/posts/${id}/like`, { method: 'POST' }),
  addComment: (id: string, text: string) =>
    request(`/api/posts/${id}/comment`, { method: 'POST', body: JSON.stringify({ text }) }),
  getUserPosts: (userId: string)     => request(`/api/posts/user/${userId}`),
};

// ── Users API ─────────────────────────────────────────────────────────────────
export const usersAPI = {
  getMe:      ()             => request('/api/users/me'),
  updateMe:   (body: any)    => request('/api/users/me', { method: 'PUT', body: JSON.stringify(body) }),
  getUser:    (id: string)   => request(`/api/users/${id}`),
  connect:    (id: string)   => request(`/api/users/${id}/connect`, { method: 'POST' }),
  search:     (q: string)    => request(`/api/users/search?q=${q}`),
};

// ── Messages API ──────────────────────────────────────────────────────────────
export const messagesAPI = {
  getChats:        ()                          => request('/api/messages/chats'),
  getConversation: (otherUserId: string)       => request(`/api/messages/${otherUserId}`),
  sendMessage:     (receiver_id: string, text: string) =>
    request('/api/messages/', { method: 'POST', body: JSON.stringify({ receiver_id, text }) }),
};

// ── Referrals API ─────────────────────────────────────────────────────────────
export const referralsAPI = {
  request:      (body: any)                    => request('/api/referrals/', { method: 'POST', body: JSON.stringify(body) }),
  myRequests:   ()                             => request('/api/referrals/my-requests'),
  myReferrals:  ()                             => request('/api/referrals/my-referrals'),
  updateStatus: (id: string, status: string)   => request(`/api/referrals/${id}/status?status=${status}`, { method: 'PUT' }),
};

// ── Notifications API ─────────────────────────────────────────────────────────
export const notificationsAPI = {
  getAll:       ()           => request('/api/notifications/'),
  unreadCount:  ()           => request('/api/notifications/unread-count'),
  markRead:     (id: string) => request(`/api/notifications/${id}/read`, { method: 'PUT' }),
  markAllRead:  ()           => request('/api/notifications/read-all', { method: 'PUT' }),
};
