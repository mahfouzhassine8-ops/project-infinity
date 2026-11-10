"""Unshipped per-call adapter for an isolated actual-source comparison.

No xbmc/module/global state is patched. The signed _context function already
accepts its read-only SDK dependency as an explicit parameter.
"""
import json
import re

SUFFIXES = ('Property(section)', 'Property(hubsource)', 'Property(Addon.ID)',
            'DBID', 'FolderPath', 'FilenameAndPath')
EXPRESSION = re.compile(r'^Container\(([1-9][0-9]*)\)\.ListItem\.(.+)$')


class LabelReader:
    def __init__(self, sdk, batch, control):
        self.sdk, self.batch = sdk, batch
        self.control = control
        self.served = set()
        self.direct_calls = 0
        self.batch_calls = 0
        self.batch_valid = False
        self.queried = False
        self.values = None

    def __getattr__(self, name):
        return getattr(self.sdk, name)

    def getInfoLabel(self, label):
        match = EXPRESSION.fullmatch(label)
        if self.batch and match and match[1] == str(self.control) and match[2] in SUFFIXES:
            labels = ['Container('+match[1]+').ListItem.'+suffix for suffix in SUFFIXES]
            if not self.queried:
                self.queried = True
                self.batch_calls += 1
                try:
                    reply = json.loads(self.sdk.executeJSONRPC(json.dumps(dict(
                        jsonrpc='2.0', id=947, method='XBMC.GetInfoLabels', params=dict(labels=labels)))))
                    result = reply.get('result')
                    if (reply.get('id') == 947 and reply.get('jsonrpc') == '2.0' and 'error' not in reply
                            and isinstance(result, dict) and all(isinstance(result.get(k), str) for k in labels)):
                        self.values = result
                        self.batch_valid = True
                except (ValueError, TypeError, AttributeError, RuntimeError):
                    pass
            if self.values is not None and label in self.values and label not in self.served:
                self.served.add(label)
                return self.values[label]
        self.direct_calls += 1
        return self.sdk.getInfoLabel(label)
