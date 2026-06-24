export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  email_verified: boolean;
  phone_masked: string;
  account_type: string;
  country: string;
  currency: string;
  two_factor_enabled: boolean;
  biometric_enabled: boolean;
  whatsapp_connected: boolean;
  telegram_connected: boolean;
}

export interface SpendConcentration {
  top_category: string | null;
  top_label: string | null;
  pct: number;
  concentrated: boolean;
}

export interface Dashboard {
  money_in: string;
  money_out: string;
  net_cash_flow: string;
  transactions: number;
  health_score: number;
  savings_rate: number;
  spend_pace: number;
  signals: {
    save: "healthy" | "watch";
    spend_concentration: SpendConcentration;
    emergency_runway_months: number;
  };
  auto_sync: {
    active: boolean;
    sources: string[];
    today_count: number;
  };
}

export interface Transaction {
  id: number;
  description: string;
  amount: string;
  direction: "in" | "out";
  category: string;
  category_label: string;
  occurred_at: string;
  source_type: string;
  source_institution: string | null;
  source_badge: string;
  is_auto_synced: boolean;
  reference: string;
  balance_after: string | null;
  confidence: number;
}

export interface Budget {
  id: number;
  name: string;
  category: string;
  category_label: string;
  monthly_limit: string;
  spent: string;
  remaining: string;
  pct_used: number;
  status: "on_track" | "over_budget";
}

export interface Goal {
  id: number;
  title: string;
  goal_type: string;
  target_amount: string;
  saved_amount: string;
  target_date: string | null;
  priority: number;
  progress_pct: number;
  is_completed: boolean;
  status: "ahead" | "on_track" | "behind" | "at_risk" | "completed";
}

export interface CashflowMonth {
  label: string;
  year: number;
  month: number;
  income: string;
  expenses: string;
  net: string;
}

export interface CategoryRow {
  category: string;
  label: string;
  amount: string;
  pct: number;
}

export interface Reports {
  health_score: number;
  net_cash_flow: string;
  savings_rate: number;
  spend_pace: number;
  cashflow_trend: CashflowMonth[];
  average_monthly_margin: string;
  category_breakdown: CategoryRow[];
  signals: {
    save: "healthy" | "watch";
    spend_concentration: SpendConcentration;
  };
}

export interface ChatLogged {
  description: string;
  amount: string;
  category: string;
  direction: string;
}

export interface ChatResponse {
  reply: string;
  logged: ChatLogged[];
  message_id: number;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface SmsSource {
  id: number;
  name: string;
  short_code: string;
  enabled: boolean;
  status: string;
  transaction_count: number;
  last_sync_at: string | null;
}
