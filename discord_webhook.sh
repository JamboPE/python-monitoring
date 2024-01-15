title="$1"
description="$2"
discord_url="$3"

#"content": "Hello! World!",
generate_post_data() {
  cat <<EOF
{
  "embeds": [{
    "title": "$title",
    "description": "$description",
    "color": "45973"
  }]
}
EOF
}

# POST request to Discord Webhook
curl -H "Content-Type: application/json" -X POST -d "$(generate_post_data)" $discord_url