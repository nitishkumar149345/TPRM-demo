from typing import Any, Dict

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from logger_config.logs import logger

# from pydantic import create_model, Field
from schema.models import Metric

from .parser import Extractor


class MetricExtractor:
    def __init__(self, file_path: str):
        """Initialize the MetricExtractor with file path and setup components."""
        self.file_path = file_path
        self.extractor = Extractor(file_path=file_path)
        self.llm = ChatOpenAI()
        self.parser = JsonOutputParser(pydantic_object=Metric)
        self.chain = self._setup_chain()
        logger.info(f"Initialized MetricExtractor for file: {file_path}")

    def _setup_chain(self) -> Any:
        """Set up the processing chain with prompt template and parser."""
        base_prompt = """
        Role: Act as an Senior Compliance Officer, experienced in analyzing service level aggrement contracts and formulating various sla metrics.
        Task: Your task is to understand, analyze and identify various SLA Performance metrics from the given SLA contract document.
        Guidelines: To perform the specified task, follow these steps:
            - Read and understand the sla metrics from the contract document.
            - Identify and classify performance metrics like uptime, response time, resolutuion_time, throughput, latency, capacity, error rate, mean_time_between_failures, and mean_time_to_repair from mentiones sla metrics in contract.
        Input: You will receive the contract as complete text: {context}
        Output: Respond with identified SLA Performance Metrics in specified format.
        \n\n
        format_instructions: {format_instructions}
        """

        prompt = ChatPromptTemplate.from_messages(
            [("system", base_prompt), ("user", "{input}")]
        )

        return prompt | self.llm | self.parser

    def process_metrics(self) -> Dict[str, Any]:
        """Process all metrics from the document and return results."""
        logger.info("Starting metrics processing")

        try:
            metadata = self.extractor.collect_data()
            metrics = self.extractor.get_fields()
            logger.info(f"Found {len(metrics)} metrics to process")

            final_metrics = {}

            for metric in metrics:
                logger.debug(f"Processing metric: {metric}")
                try:
                    data = metadata.get(metric)
                    context = "".join(chunk.page_content for chunk in data)
                    query = f"collect all data related to the metric {metric} and format in specified json"

                    response = self.chain.invoke(
                        {
                            "context": context,
                            "format_instructions": self.parser.get_format_instructions(),
                            "input": query,
                        }
                    )

                    final_metrics[metric] = {'result':response, 'source':metadata[metric]}
                  

                    logger.info(f"Successfully processed metric: {metric}")
                
                except Exception as e:
                    logger.error(f"Error processing metric {metric}: {str(e)}")
                    raise Exception

            logger.info("Completed processing all metrics")
            return final_metrics

        except Exception as e:
            logger.error(f"Failed to process metrics: {str(e)}")
            raise


def main():
    """Main function to run the metric extraction process."""
    try:
        file_path = r"C:\Users\Nitish Kumar\Desktop\TPRM_Agents\contracts\CareConnect Solutions Master Services Agreement.pdf"
        extractor = MetricExtractor(file_path)
        results = extractor.process_metrics()
        logger.info(f"Successfully extracted {len(results)} metrics")
        return results

    except Exception as e:
        logger.error(f"Main process failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
