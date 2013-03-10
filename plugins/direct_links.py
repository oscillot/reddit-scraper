#works as of 02-23-13
from base_plugin import BasePlugin


class DirectLinks(BasePlugin):
    def execute(self, candidate):
        """Executor for this plugin. The entry function by which any plugin must
        operate to handle links.
        :param dict candidate: data from a reddit post json
        """
        for img_type in ['.jpg', '.jpeg', '.gif', '.bmp', '.png']:
            if candidate['data']['url'].lower().rsplit('?')[0].endswith(
                    img_type):
                self.to_acquire.append({'url': candidate['data']['url']
                    .rsplit('?')[0],
                    'subreddit': candidate['data']['subreddit'],
                    'title': candidate['data']['title']})
                self.handled.append(candidate)
                break