def execute(children, candidates):
    handled = []
    for child in children:
        for img_type in ['.jpg', '.jpeg', '.gif', '.bmp', '.png']:
            if child['data']['url'].lower().rsplit('?')[0].endswith(img_type):
                candidates.append({'url' : child['data']['url'],
                                   'subreddit' : child['data']['subreddit'],
                                   'title' : child['data']['title']})
                handled.append(child)
                break
    return handled, candidates