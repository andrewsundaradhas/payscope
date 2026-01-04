"""
Data processing utilities for ML pipeline
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any


class DataProcessor:
    """
    Base class for data preprocessing
    """
    
    def __init__(self):
        self.fitted = False
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load data from file
        
        Args:
            file_path: Path to data file
            
        Returns:
            DataFrame with loaded data
        """
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
    
    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the data
        
        Args:
            data: Raw data
            
        Returns:
            Preprocessed data
        """
        # TODO: Add your preprocessing logic
        return data
    
    def fit_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Fit the processor and transform data
        
        Args:
            data: Raw data
            
        Returns:
            Transformed data
        """
        # TODO: Add your fit and transform logic
        self.fitted = True
        return self.preprocess(data)
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform data using fitted processor
        
        Args:
            data: Raw data
            
        Returns:
            Transformed data
        """
        if not self.fitted:
            raise ValueError("Processor must be fitted before transform")
        
        return self.preprocess(data)

