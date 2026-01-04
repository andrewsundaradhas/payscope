"""
Base ML model class
"""
from abc import ABC, abstractmethod
import joblib
from pathlib import Path
from typing import Any, Dict


class BaseModel(ABC):
    """
    Abstract base class for ML models
    """
    
    def __init__(self, model_path: str = None):
        self.model = None
        self.model_path = model_path
        self.is_trained = False
    
    @abstractmethod
    def train(self, X, y):
        """
        Train the model
        
        Args:
            X: Training features
            y: Training labels
        """
        pass
    
    @abstractmethod
    def predict(self, X):
        """
        Make predictions
        
        Args:
            X: Features for prediction
            
        Returns:
            Predictions
        """
        pass
    
    def save_model(self, path: str = None):
        """
        Save the trained model
        
        Args:
            path: Path to save the model
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        save_path = path or self.model_path
        if not save_path:
            raise ValueError("Model path must be specified")
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, save_path)
        print(f"Model saved to {save_path}")
    
    def load_model(self, path: str = None):
        """
        Load a trained model
        
        Args:
            path: Path to load the model from
        """
        load_path = path or self.model_path
        if not load_path:
            raise ValueError("Model path must be specified")
        
        if not Path(load_path).exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")
        
        self.model = joblib.load(load_path)
        self.is_trained = True
        print(f"Model loaded from {load_path}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model_type": self.__class__.__name__,
            "is_trained": self.is_trained,
            "model_path": self.model_path
        }

