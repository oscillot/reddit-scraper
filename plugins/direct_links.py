#works as of 02-23-13


def execute(candidates, to_acquire):
    """Executor for this plugin. The entry function by which any plugin must
    operate to handle links.

    :param list candidates: a list of dictionaries converted from the json
    response given back by reddit.
    :rtype list, list: a list of the dictionary data that was successfully
    parsed by this plugin, a list of dictionaries with the url,
    subreddit and title of the direct link for later acquisition and database
     entry
    """
    handled = []
    for cand in candidates:
        for img_type in ['.jpg', '.jpeg', '.gif', '.bmp', '.png']:
            if cand['data']['url'].lower().rsplit('?')[0].endswith(img_type):
                to_acquire.append({'url': cand['data']['url'].rsplit('?')[0],
                                   'subreddit': cand['data']['subreddit'],
                                   'title': cand['data']['title']})
                handled.append(cand)
                break
    return handled, to_acquire