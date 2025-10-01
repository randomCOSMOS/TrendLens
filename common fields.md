# Common fields (web_profile_info)

`data.user.username` → username (string)

`data.user.full_name` → display name / full name (string)

`data.user.biography` → bio text (string)

`data.user.external_url` → website link in profile (string or null)

`data.user.is_private` → boolean (is account private)

`data.user.is_verified` → boolean (verified badge)

`data.user.is_business_account` → boolean (business/creator flag)

`data.user.profile_pic_url` → profile image (standard)

`data.user.profile_pic_url_hd` → profile image (high resolution)

# Follower / Following / Posts (counts)

`data.user.edge_followed_by.count` → followers (total follower count)

`data.user.edge_follow.count` → following (how many accounts they follow)

`data.user.edge_owner_to_timeline_media.count` → total posts (number of timeline posts)

# Other useful edges / metadata you may see

`data.user.edge_owner_to_timeline_media.edges` → array of recent media nodes (each node has id, shortcode, display_url, etc.)

`data.user.highlight_reel_count` → number of story highlights (sometimes present)

`data.user.has_channel` / `data.user.is_private` → extra flags about account features