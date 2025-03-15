#!/usr/bin/env python3
"""
Knowledge Tools Module

This module provides tools for querying and analyzing past automation knowledge
from activity logs.
"""

import os
import json
from typing import Dict, Any, List
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI 
from langchain_core.prompts import ChatPromptTemplate

# Import from core modules
from core.logger import query_logs

@tool
def query_application_knowledge(query: str) -> str:
    """
    Query past activity logs to answer questions about the application's behavior.
    
    This tool searches through activity logs and uses an LLM to analyze them
    and provide human-readable answers to questions about past automation runs.
    
    Args:
        query (str): The question to answer about past automation activities
    
    Returns:
        str: LLM-generated response to the query based on activity logs
    """
    print(f"\n=== Querying Application Knowledge: {query} ===")
    
    try:
        # Get log data from the logger
        log_data = query_logs()
        
        if "No activity logs found" in log_data or "contains no entries" in log_data:
            return "No activity logs available to answer your query."
        
        # Initialize LLM
        model = ChatOpenAI(model="gpt-3.5-turbo")
        
        # Create prompt for the LLM
        template = """
        You are an expert Android automation analyst. You have access to logs from 
        past automation runs and need to answer questions about them.
        
        Here are the activity logs:
        {log_data}
        
        User question: {query}
        
        Based on the provided logs, answer the user's question as accurately as possible. 
        If the logs don't contain information to answer the question, say so.
        Provide a detailed, helpful analysis based on the available data.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Create LLM chain
        chain = prompt | model
        
        # Run the chain
        print("Running LLM analysis on logs...")
        response = chain.invoke({"log_data": log_data, "query": query})
        
        # Output the LLM's response
        print(f"LLM Response: {response.content}")
        
        return response.content
        
    except Exception as e:
        error_msg = f"Error querying application knowledge: {str(e)}"
        print(f"Exception: {error_msg}")
        return error_msg
