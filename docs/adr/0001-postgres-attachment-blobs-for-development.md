# PostgreSQL attachment blobs for development

For the development phase, DayStack stores an Attachment's private binary content in a one-to-one Attachment blob record in PostgreSQL instead of using S3-compatible object storage. Static images are server-compressed to WebP with an 800 KB target and a 1 MB hard limit; a later production migration will move Attachment blobs to private object storage. The migration retains legacy object-storage metadata so that later work can locate existing files without exposing those keys to the application.
