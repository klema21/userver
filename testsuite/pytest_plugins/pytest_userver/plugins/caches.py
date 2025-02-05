"""
Fixtures for controlling userver caches.
"""
import copy
import typing

import pytest


class CacheConfig:
    def __init__(self):
        self.incremental_caches = set()

    def register_incremental_cache(self, *names):
        self.incremental_caches.update(names)


class UserverCacheHookspec:
    def pytest_userver_caches_setup(
            self, userver_cache_config: CacheConfig,
    ) -> None:
        pass


class InvalidationState:
    def __init__(self, cache_config: CacheConfig):
        # None means that we should update all caches.
        # We invalidate all caches at the start of each test.
        self._invalidated_caches: typing.Optional[typing.Set[str]] = None
        self._cache_config = cache_config

    def invalidate_all(self) -> None:
        self._invalidated_caches = None

    def invalidate(self, caches: typing.Iterable[str]) -> None:
        if self._invalidated_caches is not None:
            self._invalidated_caches.update(caches)

    @property
    def should_update_all_caches(self) -> bool:
        return self._invalidated_caches is None

    @property
    def caches_to_update(self) -> typing.FrozenSet[str]:
        assert self._invalidated_caches is not None
        return frozenset(self._invalidated_caches)

    @property
    def has_caches_to_update(self) -> bool:
        caches = self._invalidated_caches
        return caches is None or bool(caches)

    @property
    def incremental_caches(self):
        return tuple(self._cache_config.incremental_caches)

    def on_caches_updated(self, caches: typing.Iterable[str]) -> None:
        if self._invalidated_caches is not None:
            self._invalidated_caches.difference_update(caches)

    def on_all_caches_updated(self) -> None:
        self._invalidated_caches = set()

    def assign_copy(self, other: 'InvalidationState') -> None:
        # pylint: disable=protected-access
        self._invalidated_caches = copy.deepcopy(other._invalidated_caches)


@pytest.fixture
def cache_invalidation_state(
        userver_cache_config: CacheConfig,
) -> InvalidationState:
    """
    A fixture for notifying the service of changes in cache data sources.

    Intended to be used by other fixtures that represent those data sources,
    not by tests directly.

    @ingroup userver_testsuite_fixtures
    """
    return InvalidationState(userver_cache_config)


@pytest.fixture(name='userver_cache_config', scope='session')
def _userver_cache_config(pytestconfig) -> CacheConfig:
    cache_config = CacheConfig()
    pytestconfig.pluginmanager.hook.pytest_userver_caches_setup(
        userver_cache_config=cache_config,
    )
    return cache_config


def pytest_addhooks(pluginmanager):
    pluginmanager.add_hookspecs(UserverCacheHookspec)
