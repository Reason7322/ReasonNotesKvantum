# Current-operation Sync Status Design

Desktop status must describe the operation the user just requested. Exhausted
historical receipts remain durable and individually recoverable, but cannot turn
a successful independent import/transfer into a generic current-operation error.
No protocol, UI layout, note model, or historical evidence is removed.
