import asyncio
from PySide6.QtCore import QRunnable, QObject, Signal, Slot
from core.workflow import AIBOSWorkflow

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
        self.workflow = AIBOSWorkflow(ui_broker=None)

    @Slot()
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            if self.action == "process_outgoing":
                result = loop.run_until_complete(
                    self.workflow.process_outgoing_request(
                        self.kwargs['destination_id'], 
                        self.kwargs['request_text']
                    )
                )
                self.signals.finished.emit(result)
            elif self.action == "process_incoming":
                result = loop.run_until_complete(
                    self.workflow.process_incoming_payload(self.kwargs['package_data'])
                )
                self.signals.finished.emit(result)
            elif self.action == "process_response":
                # NEW: Handles decrypting the response sent back by the destination unit
                result = loop.run_until_complete(
                    self.workflow.process_response_payload(self.kwargs['package_data'])
                )
                self.signals.finished.emit(result)
            else:
                self.signals.error.emit(f"Unknown action: {self.action}")
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            loop.close()