name: Sync & clean ONE blog article (manual)

on:
  workflow_dispatch:
    inputs:
      source_repo:
        description: 'Source repo "owner/name" (read-only), e.g. robodevelopers/robocamp-new-web'
        required: true
        default: 'robodevelopers/robocamp-new-web'
        type: string
      source_ref:
        description: 'Source branch/ref, e.g. master'
        required: true
        default: 'master'
        type: string
      source_path:
        description: 'Path to source markdown in source repo, e.g. data/blogposts/pl/lego-science-recenzja/content.md'
        required: true
        type: string

      target_path:
        description: 'Path to output file in THIS repo, e.g. blog/articles/lego-science-review/pl/full.md'
        required: true
        type: string

      language:
        description: 'pl or en'
        required: true
        type: choice
        options:
          - pl
          - en

      article_id:
        description: 'Stable article id used in knowledge-base (you can keep it same as EN slug), e.g. lego-science-review'
        required: true
        type: string

      web_slug:
        description: 'Web slug for this language, e.g. lego-science-recenzja'
        required: true
        type: string

      title:
        description: 'Article title (for frontmatter)'
        required: true
        type: string

      authors:
        description: 'Comma-separated authors, e.g. Dominika Skrzypek, Ola Syrocka'
        required: true
        type: string

      canonical_url:
        description: 'Full canonical URL (used also to expand #anchors), e.g. https://www.robocamp.pl/pl/blog/lego-science-recenzja/'
        required: true
        type: string

      published:
        description: 'Published date YYYY-MM-DD'
        required: true
        type: string

      license:
        description: 'Optional. Default CC BY-NC 4.0'
        required: false
        default: 'CC BY-NC 4.0'
        type: string

      status:
        description: 'Optional. Default published'
        required: false
        default: 'published'
        type: string

      debug:
        description: 'Print debug stats'
        required: false
        default: 'true'
        type: boolean

jobs:
  sync_clean_one:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout knowledge-base
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Checkout source repo (read-only)
        uses: actions/checkout@v4
        with:
          repository: ${{ inputs.source_repo }}
          ref: ${{ inputs.source_ref }}
          path: _source_repo
          token: ${{ secrets.ROBOCAMP_NEW_WEB_PAT }}

      - name: Run cleaner
        run: |
          set -euo pipefail
          SRC="_source_repo/${{ inputs.source_path }}"
          OUT="${{ inputs.target_path }}"

          python tools/cleaner/clean_one.py \
            --src "$SRC" \
            --out "$OUT" \
            --article-id "${{ inputs.article_id }}" \
            --web-slug "${{ inputs.web_slug }}" \
            --language "${{ inputs.language }}" \
            --title "${{ inputs.title }}" \
            --authors "${{ inputs.authors }}" \
            --canonical-url "${{ inputs.canonical_url }}" \
            --published "${{ inputs.published }}" \
            --license "${{ inputs.license }}" \
            --status "${{ inputs.status }}" \
            $([[ "${{ inputs.debug }}" == "true" ]] && echo "--debug" || true)

      - name: Commit changes
        run: |
          set -euo pipefail
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          git add "${{ inputs.target_path }}"

          if git diff --cached --quiet; then
            echo "No changes to commit."
            exit 0
          fi

          git commit -m "Sync & clean: ${{ inputs.article_id }} (${{ inputs.language }})"
          git push
