from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from constants import keys
from typing import List
from schema import models
from logger_config.logs import logger



class AnalyzeMetrics:
    """
    A class to analyze and compare SLA metrics between target and actual performance.
    
    This class uses OpenAI's language model to evaluate SLA compliance by comparing
    target metrics against actual performance metrics.
    """
    
    def __init__(self, target_metrics: dict, actual_metrics: dict):
        """
        Initialize the AnalyzeMetrics class.
        
        Args:
            target_metrics (dict): Dictionary containing target SLA metrics
            actual_metrics (dict): Dictionary containing actual performance metrics
        """
        self.target_metrics = target_metrics
        self.actual_metrics = actual_metrics
        logger.info(f"Initialized AnalyzeMetrics with {len(target_metrics)} metrics to analyze")

    def _get_prompt(self):
        """
        Create and return a ChatPromptTemplate for SLA evaluation.
        
        Returns:
            ChatPromptTemplate: A template for generating SLA evaluation prompts
        """
        base_prompt = ''' 

        You are an expert SLA Evaluator. You have to compare actual sla metric with target metric and define whether any vailation occured.
        Given the following SLA metrics:

        Target SLA:
        {target_metric}

        Actual Performance:
        {actual_metric}

        Please analyze the differences, identify breaches and generate comparision json result as specified, follow format instructuin for result comparision.
        Format Instructions:{format_instructions}
         '''
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", base_prompt),
            ('user','{input}')
        ])

        return prompt

    def analyze(self) -> List[dict]:
        """
        Analyze all metrics and generate comparison results.
        
        Returns:
            List[dict]: List of comparison results for each metric
        """
        logger.info("Starting metric analysis")
        output_parser = JsonOutputParser(pydantic_object=models.ComparisonModel)
        format_instructions = output_parser.get_format_instructions()

        prompt = self._get_prompt()
        chain = prompt | ChatOpenAI(openai_api_key=keys.OPENAI_API_KEY) | output_parser

        results = {}
        for metric in self.target_metrics.keys():
            logger.info(f"Analyzing metric: {metric}")
            target_metric = self.target_metrics[metric]
            actual_metric = self.actual_metrics[metric]
            
            try:
                result = chain.invoke({
                    "target_metric": target_metric,
                    "actual_metric": actual_metric,
                    "format_instructions": format_instructions,
                    'input': 'compare actual metric with target and generate comparsion json as specified'
                })
                results[metric] = result
                logger.debug(f"Successfully analyzed {metric}")
            except Exception as e:
                logger.error(f"Error analyzing metric {metric}: {str(e)}")
                raise

        logger.info(f"Completed analysis of {len(results)} metrics")
        return results

# Example usage and test data
if __name__ == '__main__':
    target_metrics = {}
    actual_metrics = {}
    logger.info("Starting SLA analysis script")
    try:
        agent = AnalyzeMetrics(target_metrics=target_metrics, actual_metrics=actual_metrics)
        results = agent.analyze()
        logger.info("Analysis completed successfully")
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

