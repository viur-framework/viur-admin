from PySide import QtCore
import weakref
import logging

"""
	Just a small EventDispatcher to distribute application-wide events.
"""

class EventWrapper( QtCore.QObject ):
	"""
		This is the actual class getting added to the queues.
		It monitors that its parent object stayes alive and removes
		and destroyes itself if its parent gets destroyed.
	"""
	
	def __init__(self, signal, targetFunc ):
		super( EventWrapper, self ).__init__()
		self.logger = logging.getLogger("EventWrapper")
		self.signal = signal
		self.targetFuncSelf = weakref.ref( targetFunc.__self__)
		self.targetFuncName = targetFunc.__name__
	
	def emitUsingParams(self, *args):
		"""
			Emits the stored event using the given params
		"""
		s = self.targetFuncSelf()
		if s:
			getattr( s, self.targetFuncName )( *args )
	
	def isDead( self ):
		return( self.targetFuncSelf()==None )

class EventDispatcher(  QtCore.QObject ):
	"""
		Our global EventDispatcher.
		This is extended to allow registering events by priority.
		
		*Warning:* If connecting using connectWithPriority, its not guranteed that youll ever recive events.
		Its possible for objects earlyer in the queue to stop distributing the event using StopIteration.
	"""
	highestPriority = 1
	highPriority = 2
	normalPriority = 3
	lowPriority = 4
	lowestPriority = 5
	eventMap = {}
	
	def connectWithPriority( self, signal, func, priority ):
		"""
			Connects the given function to the given event, using priority=#.
		"""
		if not signal in EventDispatcher.eventMap.keys():
			EventDispatcher.eventMap[ signal ] = {	"high": [], 
									"normal": [], 
									"low": []
									}
		obj = EventWrapper( signal, func )
		if priority == self.highestPriority: #Put this one first
			EventDispatcher.eventMap[ signal ][ "high" ].insert(0, obj)
		elif priority == self.highPriority: #Append to "high"
			EventDispatcher.eventMap[ signal ][ "high" ].append( obj )
		elif priority == self.normalPriority: #Append to "normal"
			EventDispatcher.eventMap[ signal ][ "normal" ].append( obj )
		elif priority == self.lowPriority: #Prepend to "low"
			EventDispatcher.eventMap[ signal ][ "low" ].insert( 0, obj )
		elif priority == self.lowestPriority: #Append to "low"
			EventDispatcher.eventMap[ signal ][ "low" ].append( obj )

	def emit(self, signal, *args ):
		#super( EventDispatcher, self ).emit( signal, *args )
		if signal in EventDispatcher.eventMap.keys():
			try:
				for e in EventDispatcher.eventMap[ signal ]["high"]:
					if e.isDead():
						EventDispatcher.eventMap[ signal ]["high"].remove( e )
					else:
						e.emitUsingParams( *args )
				for e in EventDispatcher.eventMap[ signal ]["normal"]:
					if e.isDead():
						EventDispatcher.eventMap[ signal ]["normal"].remove( e )
					else:
						e.emitUsingParams( *args )
				for e in EventDispatcher.eventMap[ signal ]["low"]:
					if e.isDead():
						EventDispatcher.eventMap[ signal ]["low"].remove( e )
					else:
						e.emitUsingParams( *args )
			except StopIteration:
				pass
	

event = EventDispatcher()

