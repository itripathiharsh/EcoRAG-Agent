---
title: EcoRAG Agent
emoji: 🌿
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "4.24.0"
app_file: app.py
pinned: false
---

# EcoRAG Agent

Professional AI Assistant for Environmental Questions with Multi-LLM Fallback

## Features

- **Multi-LLM Architecture**: Groq + Gemini with automatic failover
- **RAG Pipeline**: 4-step workflow (Plan → Retrieve → Answer → Reflect)
- **Professional UI**: Clean, business-appropriate interface
- **Real-time Monitoring**: Live system status and performance metrics
- **Environmental Focus**: Climate change, renewable energy, sustainability

## Setup

1. **API Keys**: Set in Hugging Face Space Settings → Repository secrets
   - `GROQ_API_KEY` (required)
   - `GEMINI_API_KEY` (required)
   - Optional backups: `GROQ_API_KEY_2`, `GEMINI_API_KEY_2`, etc.

2. **The app will automatically load** and be ready for questions

## Usage

- Ask questions about renewable energy, climate change, sustainability
- Click sample questions for quick testing
- View real-time system status and performance metrics
- Get quality evaluations for each answer

## Architecture

- **Plan**: Analyze query intent
- **Retrieve**: Search ChromaDB knowledge base  
- **Generate**: Multi-LLM with automatic failover
- **Reflect**: Quality evaluation and relevance check

Built with LangGraph, ChromaDB, Groq, and Gemini.