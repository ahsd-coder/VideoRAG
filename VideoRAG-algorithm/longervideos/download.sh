#!/bin/bash

set -ex

# courses="0-fights-in-animal-kingdom 1-nature-scenes 2-climate-week-at-columbia-engineering 3-black-myth-wukong 4-rag-lecture 5-ai-agent-lecture 6-daubechies-wavelet-lecture 7-daubechies-art-and-mathematics-lecture 8-tech-ceo-lecture 9-dspy-lecture 10-trading-for-beginners 11-primetime-emmy-awards 12-journey-through-china 13-fia-awards 14-education-united-nations 15-game-awards 16-ahp-superdecision 17-decision-making-science 18-elon-musk 19-jeff-bezos 20-12-days-of-openai 21-autogen"
courses="13-fia-awards 14-education-united-nations 15-game-awards 16-ahp-superdecision 17-decision-making-science 18-elon-musk 19-jeff-bezos 20-12-days-of-openai 21-autogen"

# Anti-detection measures for China network environment
PROXY="socks5://127.0.0.1:7893"
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

for course in $courses; do
    mkdir -p ./$course/videos
    yt-dlp  --proxy "$PROXY" \
            --user-agent "$USER_AGENT" \
            --add-header "Accept-Language:en-US,en;q=0.9" \
            --add-header "Accept-Encoding:gzip, deflate, br" \
            --add-header "Sec-Ch-Ua:\"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"" \
            --add-header "Sec-Ch-Ua-Mobile:?0" \
            --add-header "Sec-Ch-Ua-Platform:\"Windows\"" \
            --extractor-retries 10 \
            --fragment-retries 10 \
            --sleep-requests 1 \
            --max-sleep-interval 5 \
            --js-runtimes node \
            --remote-components ejs:npm \
            -o "%(id)s.%(ext)s" \
            -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]" \
            -S "vcodec:h264" \
            -a "./$course/videos.txt" \
            -P "./$course/videos" \
            --cookies "/home/gjw/VideoRAG-main/VideoRAG-algorithm/longervideos/cookies.txt" >> ./download_log.txt 2>&1
    wait
done
