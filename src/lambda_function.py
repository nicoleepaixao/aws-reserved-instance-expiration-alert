import os
import json
from datetime import datetime, timezone, timedelta
import boto3

SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
REGION = os.environ.get("REGION", os.environ.get("AWS_REGION", "us-east-1"))
THRESHOLD_DAYS = sorted([int(x.strip()) for x in os.environ.get("THRESHOLD_DAYS", "60,30,7").split(",")])

ec2 = boto3.client("ec2", region_name=REGION)
rds = boto3.client("rds", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

def _to_datetime(value):
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)

def list_ec2_reserved_instances():
    paginator = ec2.get_paginator("describe_reserved_instances")
    items = []
    for page in paginator.paginate(Filters=[{"Name": "state", "Values": ["active"]}]):
        items.extend(page["ReservedInstances"])
    return items

def list_rds_reserved_instances():
    paginator = rds.get_paginator("describe_reserved_db_instances")
    items = []
    for page in paginator.paginate():
        for ri in page["ReservedDBInstances"]:
            if ri["State"] == "active":
                items.append(ri)
    return items

def build_message(items):
    if not items:
        return (
            "Reserved Instance Expiration Alert\n\n"
            "No Reserved Instances are within the configured thresholds."
        )

    lines = [
        "Reserved Instance Expiration Alert\n",
        f"Thresholds: {THRESHOLD_DAYS}\n",
    ]

    for item in sorted(items, key=lambda x: x["days_remaining"]):
        lines.append(
            f"- Service: {item['service']}\n"
            f"  Reservation ID: {item['reservation_id']}\n"
            f"  Instance Type: {item['instance_type']}\n"
            f"  Scope: {item['scope']}\n"
            f"  Info: {item['region_info']}\n"
            f"  End Date: {item['end_date']}\n"
            f"  Days Remaining: {item['days_remaining']}\n"
        )
    return "\n".join(lines)

def lambda_handler(event, context):
    now = datetime.now(timezone.utc)

    results = []

    # EC2
    for ri in list_ec2_reserved_instances():
        end_dt = _to_datetime(ri["End"])
        days = (end_dt - now).days
        if any(days <= t for t in THRESHOLD_DAYS) and days >= 0:
            results.append({
                "service": "EC2",
                "reservation_id": ri["ReservedInstancesId"],
                "instance_type": ri["InstanceType"],
                "scope": ri["Scope"],
                "region_info": ri.get("AvailabilityZone", "Region"),
                "end_date": end_dt.isoformat(),
                "days_remaining": days,
            })

    # RDS
    for ri in list_rds_reserved_instances():
        start_dt = _to_datetime(ri["StartTime"])
        end_dt = start_dt + timedelta(seconds=ri["Duration"])
        days = (end_dt - now).days
        if any(days <= t for t in THRESHOLD_DAYS) and days >= 0:
            results.append({
                "service": "RDS",
                "reservation_id": ri["ReservedDBInstanceId"],
                "instance_type": ri["DBInstanceClass"],
                "scope": ri["ProductDescription"],
                "region_info": f"MultiAZ={ri['MultiAZ']}",
                "end_date": end_dt.isoformat(),
                "days_remaining": days,
            })

    message = build_message(results)

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"Reserved Instance Expiration Alert ({len(results)} items)",
        Message=message
    )

    return {"statusCode": 200, "body": json.dumps({"count": len(results)})}
