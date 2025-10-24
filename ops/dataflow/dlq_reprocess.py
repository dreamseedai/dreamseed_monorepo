"""
Skeleton: DLQ reprocess pipeline
 - Read from DLQ Pub/Sub
 - Optionally validate/transform/fix
 - Re-publish to original topic or write to BQ quarantine
"""

import json
import argparse
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--dlq_subscription", required=True)
    parser.add_argument("--output_topic", required=False)
    parser.add_argument("--quarantine_table", required=False)
    args, beam_args = parser.parse_known_args(argv)

    opts = PipelineOptions(beam_args, save_main_session=True, streaming=True)
    StandardOptions(opts).streaming = True

    with beam.Pipeline(options=opts) as p:
        msgs = p | "ReadDLQ" >> beam.io.ReadFromPubSub(subscription=args.dlq_subscription, with_attributes=False)

        if args.output_topic:
            msgs | "WriteFixedToTopic" >> beam.io.WriteToPubSub(topic=args.output_topic)

        # else: extend to write to BQ quarantine table


if __name__ == "__main__":
    run()

