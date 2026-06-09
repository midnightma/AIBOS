import asyncio
from PySide6.QtCore import QRunnable, QObject, Signal, Slot
import api.routes  # Import the global API routing module to access the shared workflow

class WorkerSignals(QObject):
    finished = Signal(dict)
    error = Signal(str)

class AsyncCoreWorker(QRunnable):
    """Executes existing async AIBOS core methods in a background Qt thread."""
    def __init__(self, action: str, **kwargs):
        super().__init__()
        self.action = action
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        # FIX: Fetch the globally initialized workflow (which already contains the AI model 
        # and the UI Broker) instead of instantiating a new one.
        workflow = api.routes.workflow_instance
        
        if not workflow:
            self.signals.error.emit("Workflow engine not initialized globally.")
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if self.action == "process_outgoing":
                result = loop.run_until_complete(
                    workflow.process_outgoing_request(
                        self.kwargs['destination_id'], 
                        self.kwargs['request_text']
                    )
                )
                self.signals.finished.emit(result)
            elif self.action == "process_incoming":
                result = loop.run_until_complete(
                    workflow.process_incoming_payload(self.kwargs['package_data'])
                )
                self.signals.finished.emit(result)
            elif self.action == "process_response":
                result = loop.run_until_complete(
                    workflow.process_response_payload(self.kwargs['package_data'])
                )
                self.signals.finished.emit(result)
            else:
                self.signals.error.emit(f"Unknown action: {self.action}")
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            loop.close()