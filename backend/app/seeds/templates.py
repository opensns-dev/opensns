import json

from sqlmodel import Session, select

from app.models.models import (
    Template,
    TemplateIndustry,
    TemplateLayout,
    TemplatePlatform,
)

TEMPLATES = [
    # ===== BEAUTY =====
    {
        "name": "Beauty Glow - Instagram",
        "description": "Radiant skin product showcase with soft lighting aesthetic",
        "industry": TemplateIndustry.BEAUTY,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "Unlock Your Natural Glow",
            "body": "Transform your skincare routine with clinically proven ingredients that deliver visible results in just 14 days.",
            "cta": "Shop Now",
        },
        "style_config": {
            "tone": "luxurious",
            "colors": ["#F5E6D3", "#D4A574", "#8B6F47"],
            "mood": "soft-glow",
        },
    },
    {
        "name": "Beauty Carousel - Facebook",
        "description": "Multi-step beauty routine walkthrough for Facebook feed",
        "industry": TemplateIndustry.BEAUTY,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.CAROUSEL,
        "copy_template": {
            "headline": "Your 3-Step Glow Routine",
            "body": "Cleanse, treat, and protect — our dermatologist-approved routine works for every skin type.",
            "cta": "Learn More",
        },
        "style_config": {
            "tone": "educational",
            "colors": ["#FFE4E1", "#FF69B4", "#DB7093"],
            "mood": "clean",
        },
    },
    {
        "name": "Beauty Performance - Google Ads",
        "description": "High-converting beauty product ad for search and display",
        "industry": TemplateIndustry.BEAUTY,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Award-Winning Skincare | Free Shipping",
            "body": "Rated #1 by dermatologists. 30-day money-back guarantee.",
            "cta": "Order Today",
        },
        "style_config": {
            "tone": "direct",
            "colors": ["#FFFFFF", "#000000", "#C9A96E"],
            "mood": "premium",
        },
    },
    {
        "name": "뷰티 스킨케어 - 네이버",
        "description": "네이버 GFA 최적화 뷰티 스킨케어 광고 템플릿",
        "industry": TemplateIndustry.BEAUTY,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.PRODUCT_HERO,
        "copy_template": {
            "headline": "피부과 전문의가 추천하는 스킨케어",
            "body": "임상 테스트 완료, 2주 만에 피부 톤 개선 효과를 경험하세요.",
            "cta": "자세히 보기",
        },
        "style_config": {
            "tone": "trustworthy",
            "colors": ["#FFF5F5", "#E8B4B8", "#6B4C4C"],
            "mood": "clean-korean",
        },
    },
    # ===== HEALTH =====
    {
        "name": "Health Vitality - Instagram",
        "description": "Clean supplement and wellness product showcase",
        "industry": TemplateIndustry.HEALTH,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.PRODUCT_HERO,
        "copy_template": {
            "headline": "Fuel Your Body Right",
            "body": "Premium vitamins and supplements backed by science. Feel the difference from day one.",
            "cta": "Try Free Sample",
        },
        "style_config": {
            "tone": "energetic",
            "colors": ["#E8F5E9", "#4CAF50", "#2E7D32"],
            "mood": "fresh",
        },
    },
    {
        "name": "Health Wellness - Facebook",
        "description": "Wellness lifestyle ad with social proof elements",
        "industry": TemplateIndustry.HEALTH,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.SPLIT_VIEW,
        "copy_template": {
            "headline": "Join 50,000+ Healthier Lives",
            "body": "Our plant-based formula is trusted by nutritionists and loved by customers worldwide.",
            "cta": "Start Today",
        },
        "style_config": {
            "tone": "community",
            "colors": ["#F1F8E9", "#8BC34A", "#558B2F"],
            "mood": "natural",
        },
    },
    {
        "name": "Health Supplement - Google Ads",
        "description": "Direct-response supplement ad for Google search",
        "industry": TemplateIndustry.HEALTH,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Clinically Proven Supplements | 60-Day Guarantee",
            "body": "Doctor-recommended. GMP certified. 100% natural ingredients.",
            "cta": "Buy Now",
        },
        "style_config": {
            "tone": "clinical",
            "colors": ["#FFFFFF", "#1565C0", "#0D47A1"],
            "mood": "trustworthy",
        },
    },
    {
        "name": "건강기능식품 - 네이버",
        "description": "네이버 검색광고 최적화 건강기능식품 템플릿",
        "industry": TemplateIndustry.HEALTH,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "식약처 인증 건강기능식품",
            "body": "하루 한 알로 건강을 챙기세요. 국내 제조, 엄격한 품질 관리.",
            "cta": "최저가 확인",
        },
        "style_config": {
            "tone": "authoritative",
            "colors": ["#E3F2FD", "#1976D2", "#0D47A1"],
            "mood": "medical-korean",
        },
    },
    # ===== FOOD =====
    {
        "name": "Food Cravings - Instagram",
        "description": "Appetite-triggering food product photography style",
        "industry": TemplateIndustry.FOOD,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "Taste the Difference",
            "body": "Handcrafted with locally sourced ingredients. Every bite tells a story of quality and care.",
            "cta": "Order Now",
        },
        "style_config": {
            "tone": "appetizing",
            "colors": ["#FFF3E0", "#FF9800", "#E65100"],
            "mood": "warm",
        },
    },
    {
        "name": "Food Story - Facebook",
        "description": "Brand story-driven food ad for Facebook engagement",
        "industry": TemplateIndustry.FOOD,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.CAROUSEL,
        "copy_template": {
            "headline": "From Farm to Your Table",
            "body": "We partner with local farmers to bring you the freshest, most flavorful ingredients possible.",
            "cta": "Discover Our Story",
        },
        "style_config": {
            "tone": "storytelling",
            "colors": ["#EFEBE9", "#795548", "#4E342E"],
            "mood": "rustic",
        },
    },
    {
        "name": "Food Delivery - Google Ads",
        "description": "Quick-converting food delivery ad for Google",
        "industry": TemplateIndustry.FOOD,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Fresh Meals Delivered | First Order 20% Off",
            "body": "Restaurant-quality meals at your door in 30 minutes. No subscription needed.",
            "cta": "Get 20% Off",
        },
        "style_config": {
            "tone": "urgent",
            "colors": ["#FFFFFF", "#D32F2F", "#FF6F00"],
            "mood": "bold",
        },
    },
    {
        "name": "맛집 배달 - 네이버",
        "description": "네이버 플레이스 및 GFA 최적화 맛집 광고",
        "industry": TemplateIndustry.FOOD,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.PRODUCT_HERO,
        "copy_template": {
            "headline": "매일 새벽 직접 공수하는 신선 재료",
            "body": "셰프가 직접 만드는 프리미엄 밀키트. 간편하게 레스토랑 맛을 집에서.",
            "cta": "지금 주문하기",
        },
        "style_config": {
            "tone": "appetizing",
            "colors": ["#FBE9E7", "#FF5722", "#BF360C"],
            "mood": "warm-korean",
        },
    },
    # ===== IT_SAAS =====
    {
        "name": "SaaS Product - Instagram",
        "description": "Modern SaaS product feature highlight for Instagram",
        "industry": TemplateIndustry.IT_SAAS,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.SPLIT_VIEW,
        "copy_template": {
            "headline": "Work Smarter, Not Harder",
            "body": "Automate repetitive tasks and focus on what matters. Trusted by 10,000+ teams.",
            "cta": "Start Free Trial",
        },
        "style_config": {
            "tone": "modern",
            "colors": ["#EDE7F6", "#7C4DFF", "#311B92"],
            "mood": "tech",
        },
    },
    {
        "name": "SaaS Demo - Facebook",
        "description": "SaaS product demo promotion for Facebook lead gen",
        "industry": TemplateIndustry.IT_SAAS,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.VIDEO_COVER,
        "copy_template": {
            "headline": "See It in Action — Free Demo",
            "body": "Streamline your workflow in minutes. No credit card required. Cancel anytime.",
            "cta": "Book a Demo",
        },
        "style_config": {
            "tone": "professional",
            "colors": ["#E8EAF6", "#3F51B5", "#1A237E"],
            "mood": "corporate",
        },
    },
    {
        "name": "SaaS Conversion - Google Ads",
        "description": "High-intent SaaS ad for Google search campaigns",
        "industry": TemplateIndustry.IT_SAAS,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "All-in-One Platform | 14-Day Free Trial",
            "body": "Replace 5 tools with 1. SOC 2 certified. 99.9% uptime SLA.",
            "cta": "Try Free",
        },
        "style_config": {
            "tone": "conversion",
            "colors": ["#FFFFFF", "#2196F3", "#0D47A1"],
            "mood": "clean-tech",
        },
    },
    {
        "name": "SaaS 솔루션 - 네이버",
        "description": "네이버 검색광고 최적화 B2B SaaS 솔루션 템플릿",
        "industry": TemplateIndustry.IT_SAAS,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "업무 자동화 솔루션 | 무료 체험",
            "body": "반복 업무를 자동화하고 생산성을 높이세요. 1,000개 이상의 기업이 선택.",
            "cta": "무료 시작하기",
        },
        "style_config": {
            "tone": "professional",
            "colors": ["#E3F2FD", "#1565C0", "#0D47A1"],
            "mood": "tech-korean",
        },
    },
    # ===== FASHION =====
    {
        "name": "Fashion Lookbook - Instagram",
        "description": "Editorial-style fashion lookbook for Instagram feed",
        "industry": TemplateIndustry.FASHION,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.CAROUSEL,
        "copy_template": {
            "headline": "New Season, New You",
            "body": "Discover our curated collection designed for effortless style. Limited edition pieces available now.",
            "cta": "Shop the Look",
        },
        "style_config": {
            "tone": "editorial",
            "colors": ["#FAFAFA", "#212121", "#757575"],
            "mood": "minimal",
        },
    },
    {
        "name": "Fashion Sale - Facebook",
        "description": "Seasonal fashion sale with urgency for Facebook",
        "industry": TemplateIndustry.FASHION,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "Up to 50% Off — This Weekend Only",
            "body": "Premium fashion at unbeatable prices. Don't miss our biggest sale of the season.",
            "cta": "Shop Sale",
        },
        "style_config": {
            "tone": "urgent",
            "colors": ["#FCE4EC", "#E91E63", "#880E4F"],
            "mood": "bold-fashion",
        },
    },
    {
        "name": "Fashion Brand - Google Ads",
        "description": "Fashion brand awareness ad for Google Display Network",
        "industry": TemplateIndustry.FASHION,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.PRODUCT_HERO,
        "copy_template": {
            "headline": "Sustainable Fashion | Free Returns",
            "body": "Ethically made. Timeless design. Complimentary returns within 30 days.",
            "cta": "Explore Collection",
        },
        "style_config": {
            "tone": "premium",
            "colors": ["#ECEFF1", "#37474F", "#263238"],
            "mood": "sophisticated",
        },
    },
    {
        "name": "패션 신상품 - 네이버",
        "description": "네이버 쇼핑 최적화 패션 신상품 광고 템플릿",
        "industry": TemplateIndustry.FASHION,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.CAROUSEL,
        "copy_template": {
            "headline": "이번 시즌 머스트해브 아이템",
            "body": "트렌디한 디자인과 편안한 착용감. 신규 회원 15% 할인 쿠폰 증정.",
            "cta": "쿠폰 받기",
        },
        "style_config": {
            "tone": "trendy",
            "colors": ["#FFF8E1", "#FF6F00", "#E65100"],
            "mood": "vibrant-korean",
        },
    },
    # ===== EDUCATION =====
    {
        "name": "Education Course - Instagram",
        "description": "Online course promotion with social proof",
        "industry": TemplateIndustry.EDUCATION,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Master New Skills Today",
            "body": "Learn from industry experts at your own pace. Over 10,000 students enrolled.",
            "cta": "Enroll Now",
        },
        "style_config": {
            "tone": "inspiring",
            "colors": ["#E0F7FA", "#00BCD4", "#006064"],
            "mood": "bright",
        },
    },
    {
        "name": "Education Webinar - Facebook",
        "description": "Free webinar/workshop promotion for Facebook",
        "industry": TemplateIndustry.EDUCATION,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.VIDEO_COVER,
        "copy_template": {
            "headline": "Free Masterclass — Limited Spots",
            "body": "Join our live session and learn actionable strategies from top instructors. Q&A included.",
            "cta": "Reserve Your Spot",
        },
        "style_config": {
            "tone": "exclusive",
            "colors": ["#FFF8E1", "#FFC107", "#FF6F00"],
            "mood": "warm-bright",
        },
    },
    {
        "name": "Education Platform - Google Ads",
        "description": "E-learning platform ad for Google search",
        "industry": TemplateIndustry.EDUCATION,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Online Courses from $9.99 | Certificate Included",
            "body": "Accredited programs. Learn at your pace. Lifetime access.",
            "cta": "Browse Courses",
        },
        "style_config": {
            "tone": "value",
            "colors": ["#FFFFFF", "#FF9800", "#E65100"],
            "mood": "accessible",
        },
    },
    {
        "name": "온라인 교육 - 네이버",
        "description": "네이버 검색광고 온라인 강의 플랫폼 템플릿",
        "industry": TemplateIndustry.EDUCATION,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.SPLIT_VIEW,
        "copy_template": {
            "headline": "현직자가 알려주는 실무 노하우",
            "body": "취업부터 이직까지, 현업 전문가의 1:1 멘토링과 실전 프로젝트 중심 커리큘럼.",
            "cta": "수강 신청",
        },
        "style_config": {
            "tone": "practical",
            "colors": ["#E8EAF6", "#3F51B5", "#1A237E"],
            "mood": "professional-korean",
        },
    },
    # ===== REAL_ESTATE =====
    {
        "name": "Real Estate Listing - Instagram",
        "description": "Premium property listing showcase for Instagram",
        "industry": TemplateIndustry.REAL_ESTATE,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.CAROUSEL,
        "copy_template": {
            "headline": "Your Dream Home Awaits",
            "body": "Stunning views, modern design, and prime location. Schedule your private tour today.",
            "cta": "Book a Tour",
        },
        "style_config": {
            "tone": "aspirational",
            "colors": ["#F5F5F5", "#1B5E20", "#004D40"],
            "mood": "luxury",
        },
    },
    {
        "name": "Real Estate Open House - Facebook",
        "description": "Open house event promotion for Facebook",
        "industry": TemplateIndustry.REAL_ESTATE,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "Open House This Saturday",
            "body": "Tour this beautiful 3-bed, 2-bath home in a top-rated school district. Refreshments provided.",
            "cta": "RSVP Now",
        },
        "style_config": {
            "tone": "inviting",
            "colors": ["#E8F5E9", "#2E7D32", "#1B5E20"],
            "mood": "welcoming",
        },
    },
    {
        "name": "Real Estate Investment - Google Ads",
        "description": "Real estate investment opportunity ad for Google",
        "industry": TemplateIndustry.REAL_ESTATE,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Luxury Condos from $299K | Prime Location",
            "body": "Invest in premium real estate. High ROI potential. Financing available.",
            "cta": "View Listings",
        },
        "style_config": {
            "tone": "investment",
            "colors": ["#FFFFFF", "#1B5E20", "#004D40"],
            "mood": "premium-green",
        },
    },
    {
        "name": "부동산 매물 - 네이버",
        "description": "네이버 부동산 및 GFA 최적화 매물 광고 템플릿",
        "industry": TemplateIndustry.REAL_ESTATE,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.PRODUCT_HERO,
        "copy_template": {
            "headline": "강남 역세권 신축 아파트 분양",
            "body": "초역세권 프리미엄 입지. 합리적인 분양가와 다양한 평형대. 모델하우스 방문 예약.",
            "cta": "방문 예약",
        },
        "style_config": {
            "tone": "premium",
            "colors": ["#FFF8E1", "#795548", "#4E342E"],
            "mood": "luxury-korean",
        },
    },
    # ===== FINANCE =====
    {
        "name": "Finance App - Instagram",
        "description": "Fintech app promotion with trust elements",
        "industry": TemplateIndustry.FINANCE,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.SPLIT_VIEW,
        "copy_template": {
            "headline": "Take Control of Your Money",
            "body": "Track spending, set goals, and grow your savings — all in one app. Bank-level security.",
            "cta": "Download Free",
        },
        "style_config": {
            "tone": "empowering",
            "colors": ["#E8F5E9", "#388E3C", "#1B5E20"],
            "mood": "secure",
        },
    },
    {
        "name": "Finance Service - Facebook",
        "description": "Financial services trust-building ad for Facebook",
        "industry": TemplateIndustry.FINANCE,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.VIDEO_COVER,
        "copy_template": {
            "headline": "Smart Investing Made Simple",
            "body": "Start investing with as little as $5. AI-powered portfolio management. No hidden fees.",
            "cta": "Get Started",
        },
        "style_config": {
            "tone": "accessible",
            "colors": ["#E3F2FD", "#1976D2", "#0D47A1"],
            "mood": "trustworthy",
        },
    },
    {
        "name": "Finance Insurance - Google Ads",
        "description": "Insurance product ad for Google search campaigns",
        "industry": TemplateIndustry.FINANCE,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Compare Insurance Quotes in 60 Seconds",
            "body": "Save up to 40% on auto, home, and life insurance. A+ rated carriers.",
            "cta": "Get Free Quote",
        },
        "style_config": {
            "tone": "comparison",
            "colors": ["#FFFFFF", "#1565C0", "#0D47A1"],
            "mood": "direct",
        },
    },
    {
        "name": "금융 투자 - 네이버",
        "description": "네이버 검색광고 금융/투자 상품 템플릿",
        "industry": TemplateIndustry.FINANCE,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "연 수익률 8% 달성 비결",
            "body": "전문 투자 매니저의 맞춤 포트폴리오. 원금 보장형 상품도 준비되어 있습니다.",
            "cta": "무료 상담 신청",
        },
        "style_config": {
            "tone": "authoritative",
            "colors": ["#E8EAF6", "#283593", "#1A237E"],
            "mood": "finance-korean",
        },
    },
    # ===== TRAVEL =====
    {
        "name": "Travel Destination - Instagram",
        "description": "Wanderlust-inducing destination showcase for Instagram",
        "industry": TemplateIndustry.TRAVEL,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "Escape the Ordinary",
            "body": "Discover hidden gems and curated experiences. Your next adventure starts here.",
            "cta": "Explore Trips",
        },
        "style_config": {
            "tone": "adventurous",
            "colors": ["#E0F2F1", "#00897B", "#004D40"],
            "mood": "wanderlust",
        },
    },
    {
        "name": "Travel Package - Facebook",
        "description": "All-inclusive travel package promotion for Facebook",
        "industry": TemplateIndustry.TRAVEL,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.CAROUSEL,
        "copy_template": {
            "headline": "All-Inclusive Getaway from $499",
            "body": "Flights, hotel, and activities included. Book now and save 30% on early-bird pricing.",
            "cta": "Book Now",
        },
        "style_config": {
            "tone": "deal",
            "colors": ["#E1F5FE", "#0288D1", "#01579B"],
            "mood": "exciting",
        },
    },
    {
        "name": "Travel Booking - Google Ads",
        "description": "Travel booking platform ad for Google search",
        "industry": TemplateIndustry.TRAVEL,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Cheap Flights & Hotels | Best Price Guarantee",
            "body": "Compare 500+ airlines and 1M+ hotels. Free cancellation on most bookings.",
            "cta": "Search Deals",
        },
        "style_config": {
            "tone": "value",
            "colors": ["#FFFFFF", "#0277BD", "#01579B"],
            "mood": "deal-focused",
        },
    },
    {
        "name": "여행 패키지 - 네이버",
        "description": "네이버 검색광고 여행 패키지 상품 템플릿",
        "industry": TemplateIndustry.TRAVEL,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.CAROUSEL,
        "copy_template": {
            "headline": "올 여름 인기 여행지 TOP 10",
            "body": "항공+숙박 패키지 최대 40% 할인. 얼리버드 특가로 더 저렴하게 떠나세요.",
            "cta": "특가 확인",
        },
        "style_config": {
            "tone": "seasonal",
            "colors": ["#E0F7FA", "#00ACC1", "#006064"],
            "mood": "vacation-korean",
        },
    },
    # ===== PET =====
    {
        "name": "Pet Products - Instagram",
        "description": "Adorable pet product showcase for Instagram",
        "industry": TemplateIndustry.PET,
        "platform": TemplatePlatform.INSTAGRAM,
        "layout": TemplateLayout.PRODUCT_HERO,
        "copy_template": {
            "headline": "Because They Deserve the Best",
            "body": "Premium, vet-approved nutrition for your furry family member. Made with real ingredients.",
            "cta": "Shop for Pets",
        },
        "style_config": {
            "tone": "loving",
            "colors": ["#FFF3E0", "#FF8A65", "#BF360C"],
            "mood": "playful",
        },
    },
    {
        "name": "Pet Subscription - Facebook",
        "description": "Pet subscription box promotion for Facebook",
        "industry": TemplateIndustry.PET,
        "platform": TemplatePlatform.FACEBOOK,
        "layout": TemplateLayout.SPLIT_VIEW,
        "copy_template": {
            "headline": "Monthly Surprise Box for Your Pet",
            "body": "Curated toys, treats, and essentials delivered monthly. Tailored to your pet's size and preferences.",
            "cta": "Subscribe & Save",
        },
        "style_config": {
            "tone": "fun",
            "colors": ["#F3E5F5", "#AB47BC", "#6A1B9A"],
            "mood": "playful-premium",
        },
    },
    {
        "name": "Pet Store - Google Ads",
        "description": "Online pet store ad for Google search",
        "industry": TemplateIndustry.PET,
        "platform": TemplatePlatform.GOOGLE_ADS,
        "layout": TemplateLayout.TEXT_OVERLAY,
        "copy_template": {
            "headline": "Premium Pet Food | Free Delivery Over $50",
            "body": "Vet-recommended brands. Same-day delivery available. Auto-ship and save 15%.",
            "cta": "Shop Now",
        },
        "style_config": {
            "tone": "convenience",
            "colors": ["#FFFFFF", "#FF7043", "#BF360C"],
            "mood": "friendly",
        },
    },
    {
        "name": "반려동물 용품 - 네이버",
        "description": "네이버 쇼핑 최적화 반려동물 용품 광고 템플릿",
        "industry": TemplateIndustry.PET,
        "platform": TemplatePlatform.NAVER,
        "layout": TemplateLayout.SINGLE_IMAGE,
        "copy_template": {
            "headline": "수의사가 추천하는 프리미엄 사료",
            "body": "100% 자연 원료, 무항생제 인증. 우리 아이 건강을 위한 최고의 선택.",
            "cta": "최저가 비교",
        },
        "style_config": {
            "tone": "caring",
            "colors": ["#FBE9E7", "#FF8A65", "#D84315"],
            "mood": "warm-korean",
        },
    },
]


def seed_templates(session: Session) -> None:
    existing = session.exec(select(Template).limit(1)).first()
    if existing:
        return

    for i, data in enumerate(TEMPLATES):
        template = Template(
            name=data["name"],
            description=data["description"],
            industry=data["industry"],
            platform=data["platform"],
            layout=data["layout"],
            copy_template=json.dumps(data["copy_template"], ensure_ascii=False),
            style_config=json.dumps(data["style_config"], ensure_ascii=False),
            sort_order=i,
        )
        session.add(template)

    session.commit()
