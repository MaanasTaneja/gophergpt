class BaseLLM(object):
    """
    Base class for all LLMs.
    This class defines the interface that all LLMs must implement.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    def get_model(self):
        """
        Get the model name.
        This method should be implemented by subclasses to return the model name.
        """
        raise NotImplementedError("Subclasses must implement the 'get_model' method.")
