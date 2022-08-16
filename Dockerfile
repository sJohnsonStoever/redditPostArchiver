FROM alpine:3.12 AS permissions-giver

# Make sure docker-entrypoint.sh is executable, regardless of the build host.
WORKDIR /out
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

FROM alpine:3.12 AS organizer

# Things needed to run reddit-post-archiver
WORKDIR /out/usr/src/app
COPY css css
COPY credentials.yml .
COPY *.py .

# Duplicate files so the scripts could be used without .py
RUN for file in $(find . -name "*.py"); do name=$(echo $file | cut -f 2 -d '/'); ln -s -T $name $(echo $name | cut -f 1 -d '.'); done

# Executebles
WORKDIR /out/usr/local/bin
COPY --from=permissions-giver /out/docker-entrypoint.sh .

FROM python:3.8-alpine AS dependency-installer

# Install build dependencies
RUN apk --no-cache add gcc musl-dev

# Install dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

FROM dependency-installer AS runner

# Set all files
COPY --from=organizer /out /

WORKDIR /usr/src/app
ENTRYPOINT [ "docker-entrypoint.sh" ]

# Save files to /rpa
ENV DOCKER 1
VOLUME [ "/rpa" ]