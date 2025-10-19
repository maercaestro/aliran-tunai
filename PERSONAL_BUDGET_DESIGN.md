"""
Personal Budget Data Model Design
=================================

This document outlines the adaptation of the existing B2B transaction model 
for personal budgeting while maintaining backward compatibility.

EXISTING B2B SCHEMA (preserved):
{
    "wa_id": str,           # User identifier  
    "action": str,          # "sale", "purchase", "payment_received", "payment_made"
    "amount": float,        # Transaction amount
    "customer": str,        # Customer/vendor name
    "vendor": str,          # Vendor/customer name  
    "items": str,           # Items/description
    "terms": str,           # Payment terms
    "description": str,     # AI-generated description
    "category": str,        # B2B categories (OPEX, CAPEX, COGS, etc.)
    "detected_language": str,
    "timestamp": datetime,
    "date_created": str,
    "time_created": str
}

PERSONAL BUDGET ADAPTATIONS:
============================

1. ACTION MAPPING:
   B2B -> Personal Budget
   - "sale" -> "income" (salary, freelance, side hustle)
   - "purchase" -> "expense" (groceries, shopping, bills)
   - "payment_received" -> "income" (refunds, returns)
   - "payment_made" -> "expense" (bill payments, transfers)

2. NEW PERSONAL CATEGORIES:
   Instead of B2B categories (OPEX, CAPEX), use personal ones:
   - FOOD & DINING: Groceries, restaurants, food delivery
   - TRANSPORTATION: Fuel, public transport, car maintenance
   - SHOPPING: Clothes, electronics, personal items
   - BILLS & UTILITIES: Rent, electricity, internet, phone
   - ENTERTAINMENT: Movies, games, subscriptions, hobbies
   - HEALTH & FITNESS: Medical, gym, supplements
   - EDUCATION: Courses, books, training
   - TRAVEL: Flights, hotels, vacation expenses
   - SAVINGS & INVESTMENT: Transfers to savings, investments
   - INCOME: Salary, freelance, business income, gifts
   - OTHER: Miscellaneous expenses

3. NEW FIELDS TO ADD:
   - "budget_category": str    # Personal budget category
   - "is_recurring": bool      # Monthly recurring expense/income
   - "budget_month": str       # YYYY-MM for budget tracking
   - "tags": [str]            # Custom user tags
   - "location": str          # Where transaction occurred
   - "is_planned": bool       # Planned vs impulse purchase

4. BUDGET MANAGEMENT:
   New collection: "personal_budgets"
   {
       "wa_id": str,
       "month": str,          # YYYY-MM
       "category_budgets": {
           "FOOD": {"budget": 500, "spent": 0},
           "TRANSPORTATION": {"budget": 200, "spent": 0},
           # ... other categories
       },
       "total_budget": float,
       "income_goal": float,
       "savings_goal": float,
       "created_at": datetime
   }

5. GOALS & TARGETS:
   New collection: "personal_goals"
   {
       "wa_id": str,
       "goal_type": str,      # "savings", "debt_payoff", "expense_reduction"
       "target_amount": float,
       "current_amount": float,
       "target_date": str,    # YYYY-MM-DD
       "description": str,
       "is_active": bool,
       "created_at": datetime
   }

MIGRATION STRATEGY:
==================
1. Keep existing transaction schema intact
2. Add new personal budget fields with default values
3. Create mapping layer to translate B2B data to personal view
4. Use feature flags to switch between B2B and personal modes
5. Existing B2B transactions can be re-categorized for personal use

WHATSAPP BOT ADAPTATIONS:
========================
1. Change prompts from business language to personal language
2. Adapt categories in AI parsing
3. Add budget tracking responses
4. Include spending alerts and budget reminders
5. Personal financial advice instead of business metrics

FRONTEND ROUTING STRATEGY:
=========================
/                     -> Landing page with mode selector
/business            -> B2B dashboard (preserved)
/business/reports    -> B2B reports (preserved)  
/personal           -> Personal budget dashboard
/personal/expenses  -> Personal expense tracking
/personal/budgets   -> Budget management
/personal/goals     -> Financial goals
/personal/insights  -> Personal financial insights
/admin              -> Mode switching for development

This approach allows:
- Complete preservation of B2B functionality
- Gradual migration to personal budget features
- Easy switching between modes during development
- Reuse of existing infrastructure (WhatsApp bot, AI, database)
"""