import json
import argparse
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from datetime import datetime, timezone


class ParseJSON(beam.DoFn):
	def process(self, msg):
		try:
			d = json.loads(msg.decode("utf-8"))
			yield d
		except Exception as e:
			yield beam.pvalue.TaggedOutput("bad", msg)


class ValidateEvent(beam.DoFn):
	def process(self, evt):
		req = ["event_id", "occurred_at", "version", "payload", "idempotency_key"]
		if not all(k in evt for k in req):
			yield beam.pvalue.TaggedOutput("bad", json.dumps(evt).encode("utf-8"))
			return
		yield evt


class ToBQRow(beam.DoFn):
    def process(self, evt):
        p = evt["payload"]
        yield {
			"event_id": evt["event_id"],
			"occurred_at": evt["occurred_at"],
			"org_id": p["org_id"],
			"session_id": p["session_id"],
			"user_id": p["user_id"],
			"question_id": p["question_id"],
			"is_correct": p["is_correct"],
			"elapsed_ms": p["elapsed_ms"],
			"ability_before": p.get("ability_before"),
            "ability_after": p.get("ability_after"),
            "ingested_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
		}


def run(argv=None):
	parser = argparse.ArgumentParser()
	parser.add_argument("--project", required=True)
	parser.add_argument("--region", required=True)
	parser.add_argument("--input_topic", required=True)
	parser.add_argument("--dlq_topic", required=True)
	parser.add_argument("--bq_table", required=True)  # project:dataset.table
	args, beam_args = parser.parse_known_args(argv)

	opts = PipelineOptions(beam_args, save_main_session=True, streaming=True)
	StandardOptions(opts).streaming = True

	with beam.Pipeline(options=opts) as p:
		msgs = p | "Read" >> beam.io.ReadFromPubSub(topic=args.input_topic, with_attributes=False)

		parsed = msgs | "Parse" >> beam.ParDo(ParseJSON()).with_outputs("bad", main="good")
		good_msgs = parsed.good
		bad_parse = parsed.bad

		validated = good_msgs | "Validate" >> beam.ParDo(ValidateEvent()).with_outputs("bad", main="good")
		good_evts = validated.good
		bad_evts = validated.bad

		# DLQ: bad_parse + bad_evts
		(bad_parse, bad_evts) | "FlattenBad" >> beam.Flatten() | "DLQ" >> beam.io.WriteToPubSub(topic=args.dlq_topic)

		rows = good_evts | "ToBQRow" >> beam.ParDo(ToBQRow())

		rows | "WriteBQ" >> beam.io.WriteToBigQuery(
			table=args.bq_table,
			write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
			create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
			schema={
				"fields": [
					{"name": "event_id", "type": "STRING", "mode": "REQUIRED"},
					{"name": "occurred_at", "type": "TIMESTAMP", "mode": "REQUIRED"},
					{"name": "org_id", "type": "INTEGER", "mode": "REQUIRED"},
					{"name": "session_id", "type": "STRING", "mode": "REQUIRED"},
					{"name": "user_id", "type": "INTEGER", "mode": "REQUIRED"},
					{"name": "question_id", "type": "INTEGER", "mode": "REQUIRED"},
					{"name": "is_correct", "type": "BOOLEAN", "mode": "REQUIRED"},
					{"name": "elapsed_ms", "type": "INTEGER", "mode": "REQUIRED"},
					{"name": "ability_before", "type": "FLOAT"},
					{"name": "ability_after", "type": "FLOAT"},
					{"name": "ingested_at", "type": "TIMESTAMP", "mode": "REQUIRED"},
				]
			},
			timePartitioning={"type": "DAY", "field": "occurred_at"},
			clustering_fields=["org_id", "question_id"],
		)


if __name__ == "__main__":
	run()

