#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Callable, Dict, List, Any, Tuple, Union


class PriorityQueue:
	def __init__(self, *args: Any, **kwargs: Any):
		super(PriorityQueue, self).__init__()
		self._q: Dict[int, List[Tuple[Callable, Callable]]] = dict()

	def insert(
			self,
			priority: int,
			validateFunc: Callable[..., bool],
			generator: Callable) -> None:
		priority = int(priority)
		if priority not in self._q:
			self._q[priority] = []
		self._q[priority].append((validateFunc, generator))

	def select(self, *args: Any, **kwargs: Any) -> Union[Callable, None]:
		prios = sorted(list(self._q), reverse=True)
		for p in prios:
			for validateFunc, generator in self._q[p]:
				if validateFunc(*args, **kwargs):
					return generator
		return None


editBoneSelector = PriorityQueue()  # Queried by editWidget to locate its bones
viewDelegateSelector = PriorityQueue()  # Queried by listWidget to determine the viewDelegates for the table
actionDelegateSelector = PriorityQueue()  # Locates an QAction for a given module/action-name
protocolWrapperClassSelector = PriorityQueue()  # Used during startup to select an Wrapper-Class
protocolWrapperInstanceSelector = PriorityQueue()  # Used afterwards to get a specific instance
extendedSearchWidgetSelector = PriorityQueue()  # Queried for additional search filter widgets defined by server
