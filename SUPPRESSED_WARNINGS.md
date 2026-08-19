# Suppressed test warnings

`setup.cfg`'s `[tool:pytest]` `filterwarnings` uses `default` (show everything) plus explicit
`ignore` rules. This file documents *why* each ignore rule exists, so nobody re-adds one of
these warnings to CI without knowing it was a deliberate, informed choice.

All warnings listed below originate from third-party or edx-platform code loaded as part of the
LMS test app (`lms.envs.test`) — none of them are raised by code inside `tablelonginput/`. They
can't be fixed from this package: fixing them would mean patching `defusedxml`, `future`,
`PyContracts`, `newrelic`, `sorl-thumbnail`, or edx-platform itself, none of which this package
controls or pins in its own `setup.py`.

| Ignore rule (regex/category) | Source | Warning | Why it can't be fixed here |
|---|---|---|---|
| `defusedxml.lxml is no longer supported.*` (`DeprecationWarning`) | `edx-platform/common/lib/safe_lxml/safe_lxml/etree.py` | `defusedxml.lxml` is no longer supported and will be removed in a future release | edx-platform's own module; not imported by `tablelonginput` |
| `the imp module is deprecated in favour of importlib.*` (`DeprecationWarning`) | `past/builtins/misc.py` (the `future` package, a transitive dep of the test image) | the `imp` module is deprecated in favour of `importlib` | Third-party dependency pinned by edx-platform's requirements, not by `tablelonginput` |
| `Using or importing the ABCs from 'collections'...` (`DeprecationWarning`) | `contracts/library/miscellaneous_aliases.py` (PyContracts) | ABCs moved from `collections` to `collections.abc` in Python 3.3+ | Third-party dependency (`PyContracts`), not imported by `tablelonginput` |
| `` `formatargspec` is deprecated since Python 3.5.* `` (`DeprecationWarning`) | `newrelic/console.py` | `inspect.formatargspec` is deprecated | Third-party APM agent installed in the LMS test image |
| `django.utils.deprecation.RemovedInDjango30Warning` | `sorl/thumbnail/conf/__init__.py` | `DEFAULT_CONTENT_TYPE` setting is deprecated | Third-party package (`sorl-thumbnail`) reading a removed Django setting |
| `django.utils.deprecation.RemovedInDjango31Warning` | `sorl/thumbnail/conf/__init__.py` | `FILE_CHARSET` setting is deprecated | Same as above |
| `Importing .* is deprecated` | `enterprise/utils.py`, `enterprise/admin/forms.py`, `enterprise/signals.py` | `DeprecatedEdxPlatformImportWarning` — importing e.g. `student` instead of `common.djangoapps.student` | edx-platform's own `enterprise` app using legacy pre-`common.djangoapps` import paths |
| `No request passed to the backend, unable to rate-limit:UserWarning` | edx-platform auth backend | Rate-limiting is skipped because no request object was passed | Deliberate: test user logins aren't throttled on purpose |
| `xblock.exceptions.FieldDataDeprecationWarning` | XBlock runtime | Field data deprecation | Fixing requires a major, low-priority refactor of field data access across the block |

## If you see a new warning

Before adding another `ignore` rule here: check whether the warning traces back into
`tablelonginput/*.py` — if so, fix it (see the `CourseLocator` example above) rather than hiding
it. Only add an ignore rule, and a row to this table, for warnings coming from code outside this
package.
