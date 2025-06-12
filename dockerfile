# === Builder Stage ===
FROM ubuntu:20.04 AS builder

ENV TZ=Asia/Taipei
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/conda/bin:$PATH"

# Update repository and install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    gnupg \
    git \
    python3 \
    python3-pip \
    ca-certificates \
    apt-transport-https \
    software-properties-common \
    && apt-get clean

# Install conda, selenium
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh \
    && bash miniconda.sh -b -p /opt/conda \
    && rm miniconda.sh \
    && /opt/conda/bin/conda install -c defaults -c bioconda -c conda-forge -y pandas openpyxl selenium \
    && /opt/conda/bin/conda clean -afy

# Install a fixed version of Google Chrome (132.0.6834.83)
RUN wget -q -O /tmp/google-chrome-stable.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_132.0.6834.83-1_amd64.deb \
    && apt-get install -y /tmp/google-chrome-stable.deb \
    && rm -f /tmp/google-chrome-stable.deb \
    && apt-get clean

# Install a fixed version of ChromeDriver (132.0.6834.83)
RUN mkdir -p /app \
    && wget -q -O /tmp/chromedriver-linux64.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/132.0.6834.83/linux64/chromedriver-linux64.zip \
    && unzip /tmp/chromedriver-linux64.zip -d /tmp/ \
    && chmod +x /tmp/chromedriver-linux64/chromedriver \
    && mkdir -p /app/chromedriver-linux64 \
    && mv /tmp/chromedriver-linux64/chromedriver /app/chromedriver-linux64/chromedriver \
    && rm -rf /tmp/chromedriver-linux64.zip /tmp/chromedriver-linux64

# Clone repository
RUN git clone https://github.com/gaminyeh/selenium-genebots.git /tmp/repo \
    && cp -r /tmp/repo/. /app/ \
    && rm -rf /tmp/repo

# === Final Stage ===
FROM ubuntu:20.04

ENV TZ=Asia/Taipei
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/opt/conda/bin:$PATH"

# Install minimal runtime dependencies for Google Chrome & ChromeDriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    r-base \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy necessary files from builder
COPY --from=builder /opt/conda /opt/conda
COPY --from=builder /usr/bin/google-chrome /usr/bin/google-chrome
COPY --from=builder /opt/google/chrome /opt/google/chrome
COPY --from=builder /app /app

RUN ln -s /opt/google/chrome/chrome /usr/bin/chrome
RUN git config --global --add safe.directory /app

# Set working directory
WORKDIR /app
