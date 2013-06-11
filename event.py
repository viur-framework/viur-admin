from PySide import QtCore
import weakref
import logging

"""
	Just a small EventDispatcher to distribute application-wide events.
"""

class WeakFuncWrapper( ):
	def __init__( self, targetFunc ):
		super( WeakFuncWrapper, self ).__init__()
		if "__self__" in dir( targetFunc ):
			self.targetFuncSelf = weakref.ref( targetFunc.__self__)
			self.targetFuncName = targetFunc.__name__
			self.targetFunc = None
		else:
			self.targetFuncSelf = None
			self.targetFuncName = None
			self.targetFunc = weakref.ref( targetFunc )
	
	def call( self, *args, **kwargs ):
		if self.targetFuncName is not None: #Bound function
			funcSelf = self.targetFuncSelf()
			if funcSelf is not None:
				getattr( funcSelf, self.targetFuncName )( *args, **kwargs )
		else:
			tf = self.targetFunc()
			if tf is not None:
				tf( *args, **kwargs )
			
	def isDead( self ):
		if self.targetFuncName is not None: #Bound function
			return( self.targetFuncSelf() is None )
		else:
			return( self.targetFunc() is None )


class EventWrapper( QtCore.QObject ): ### REPLACED BY WEAK FUNC WRAPPER
	"""
		This is the actual class getting added to the queues.
		It monitors that its parent object stayes alive and removes
		and destroyes itself if its parent gets destroyed.
	"""
	
	def __init__(self, signal, targetFunc ):
		super( EventWrapper, self ).__init__()
		self.logger = logging.getLogger("EventWrapper")
		self.signal = signal
		self.targetFunc = WeakFuncWrapper( targetFunc )

	
	def emitUsingParams(self, *args):
		"""
			Emits the stored event using the given params
		"""
		
		s = self.targetFuncSelf()
		if s:
			getattr( s, self.targetFuncName )( *args )
	
	def isDead( self ):
		return( self.targetFuncSelf() is None )

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
		obj = WeakFuncWrapper( func )
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
						e.call( *args )
				for e in EventDispatcher.eventMap[ signal ]["normal"]:
					if e.isDead():
						EventDispatcher.eventMap[ signal ]["normal"].remove( e )
					else:
						e.call( *args )
				for e in EventDispatcher.eventMap[ signal ]["low"]:
					if e.isDead():
						EventDispatcher.eventMap[ signal ]["low"].remove( e )
					else:
						e.call( *args )
			except StopIteration:
				pass
	

event = EventDispatcher()

