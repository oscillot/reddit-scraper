#works as of 02-23-13


def execute(candidates, to_acquire):
    handled = []
    for child in candidates:
        for img_type in ['.jpg', '.jpeg', '.gif', '.bmp', '.png']:
            if child['data']['url'].lower().rsplit('?')[0].endswith(img_type):
                to_acquire.append({'url': child['data']['url'].rsplit('?')[0],
                                   'subreddit': child['data']['subreddit'],
                                   'title': child['data']['title']})
                handled.append(child)
                break
    return handled, to_acquire