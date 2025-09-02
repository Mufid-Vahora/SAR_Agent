import asyncio
import json
import os
import csv
from datetime import datetime
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from packages.shared.topics import Topics


KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")
GROUP_ID = os.getenv("PARSER_GROUP_ID", "parser-agent")
OUTPUT_TOPIC = os.getenv("PARSER_OUTPUT_TOPIC", Topics.PARSED_JSON)


def parse_pipe_file(file_path: str) -> list[dict]:
    """Parse pipe-delimited file and return structured JSON rows."""
    rows = []
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter='|')
        for i, row in enumerate(reader):
            # Add metadata
            parsed_row = {
                "row_number": i + 1,
                "raw_data": row,
                "parsed_at": datetime.now().isoformat(),
                "source_file": file_path,
                # Map common fields to standardized names
                "entity_name": row.get("EntityName", row.get("entity_name", "")),
                "entity_type": row.get("EntityType", row.get("entity_type", "")),
                "transaction_id": row.get("TransactionID", row.get("transaction_id", "")),
                "amount": float(row.get("Amount", row.get("amount", "0"))) if row.get("Amount") or row.get("amount") else 0,
                "status": row.get("Status", row.get("status", "")),
                "date": row.get("Date", row.get("date", "")),
            }
            rows.append(parsed_row)
    return rows


async def handle_ingestion(message_value: bytes, producer: AIOKafkaProducer):
    """Handle ingestion message and emit parsed JSON rows."""
    evt = json.loads(message_value.decode("utf-8"))
    job_id = evt.get("job_id")
    upload_path = evt.get("upload_path")
    
    print(f"[Parser] Processing job {job_id}, file: {upload_path}")
    
    if not upload_path or not os.path.exists(upload_path):
        print(f"[Parser] ❌ File not found: {upload_path}")
        return
    
    try:
        # Parse the pipe-delimited file
        rows = parse_pipe_file(upload_path)
        print(f"[Parser] ✅ Parsed {len(rows)} rows from {upload_path}")
        
        # Emit each row to the parsed-json topic
        for row in rows:
            payload = {
                "job_id": job_id,
                "row": row,
                "source_file": upload_path,
                "parsed_at": datetime.now().isoformat(),
            }
            await producer.send_and_wait(OUTPUT_TOPIC, json.dumps(payload).encode("utf-8"))
            print(f"[Parser] 📤 Emitted row {row['row_number']} to {OUTPUT_TOPIC}")
        
        print(f"[Parser] ✅ Completed job {job_id} - {len(rows)} rows processed")
        
    except Exception as e:
        print(f"[Parser] ❌ Error processing job {job_id}: {e}")
        # Emit error event
        error_payload = {
            "job_id": job_id,
            "error": str(e),
            "source_file": upload_path,
            "timestamp": datetime.now().isoformat(),
        }
        await producer.send_and_wait(Topics.AUDIT_EVENTS, json.dumps(error_payload).encode("utf-8"))


async def run():
    """Main consumer loop."""
    consumer = AIOKafkaConsumer(
        Topics.INGESTION,
        bootstrap_servers=KAFKA_BROKERS,
        group_id=GROUP_ID,
        enable_auto_commit=True,
        auto_offset_reset="earliest",
    )
    
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    
    print(f"[Parser] 🚀 Starting parser agent (group: {GROUP_ID})")
    print(f"[Parser] 📥 Consuming from: {Topics.INGESTION}")
    print(f"[Parser] 📤 Producing to: {OUTPUT_TOPIC}")
    
    await consumer.start()
    await producer.start()
    
    try:
        async for msg in consumer:
            await handle_ingestion(msg.value, producer)
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(run())


