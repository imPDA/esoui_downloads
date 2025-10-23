const typeIcons = {
    'Author': 'fas fa-user',
    'Library': 'fas fa-book',
    'Addon': 'fas fa-puzzle-piece',
};

let searchInput;
let resultsContainer;
let loader;
let themeToggle;
let body;

let debounceTimer;
const debounceDelay = 500;
let currentResults = [];

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'light' || (!savedTheme && !prefersDark)) {
        body.classList.add('light-theme');
        themeToggle.checked = true;
    }
    
    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            body.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
        } else {
            body.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
        }
    });
}

function debounce(func, delay) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(func, delay);
}

function performSearch() {
    const query = searchInput.value.trim();
    
    if (query.length === 0) {
        resultsContainer.style.display = 'none';
        resultsContainer.innerHTML = '';
        return;
    }
    
    if (query.length < 3) {
        resultsContainer.style.display = 'none';
        resultsContainer.innerHTML = '';
        return;
    }
    
    loader.style.display = 'block';
    
    fetch(`/api/addons?q=${encodeURIComponent(query)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(results => {
            currentResults = results;
            displayResults(results);
            loader.style.display = 'none';
        })
        .catch(error => {
            console.error('Search error:', error);
            resultsContainer.innerHTML = '<div class="no-results">Error loading results</div>';
            resultsContainer.style.display = 'block';
            loader.style.display = 'none';
        });
}

function navigateToAddon(result) {
    window.location.href = `/addon/${result.esoui_id}`;
}

function displayResults(results) {
    if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">No results found</div>';
        resultsContainer.style.display = 'block';
        return;
    }
    
    const displayCount = Math.min(results.length, 8);
    const remainingCount = results.length - displayCount;
    
    let resultsHTML = '';
    
    for (let i = 0; i < displayCount; i++) {
        const result = results[i];
        const iconClass = typeIcons['Addon'];
        
        resultsHTML += `
            <div class="result-item" data-index="${i}">
                <div class="result-icon"><i class="${iconClass}"></i></div>
                <div class="result-content">
                    <div class="result-title">${result.title}</div>
                    <div class="result-author">by ${result.author}</div>
                </div>
            </div>
        `;
    }
    
    if (remainingCount > 0) {
        resultsHTML += `<div class="more-results">~ ${remainingCount} more result${remainingCount !== 1 ? 's' : ''} hidden ~</div>`;
    }
    
    resultsContainer.innerHTML = resultsHTML;
    resultsContainer.style.display = 'block';
    
    document.querySelectorAll('.result-item').forEach(item => {
        item.addEventListener('click', () => {
            const index = parseInt(item.getAttribute('data-index'));
            const result = results[index];
            navigateToAddon(result);
        });
    });
}

function initializeEventListeners() {
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        
        if (query.length === 0) {
            resultsContainer.style.display = 'none';
            resultsContainer.innerHTML = '';
            clearTimeout(debounceTimer);
            return;
        }
        
        debounce(performSearch, debounceDelay);
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && currentResults.length === 1) {
            const result = currentResults[0];
            navigateToAddon(result);
        }
    });
}

function initializeElements() {
    searchInput = document.querySelector('.search-input');
    resultsContainer = document.getElementById('results-container');
    loader = document.getElementById('loader');
    themeToggle = document.getElementById('theme-toggle');
    body = document.body;
    
    if (!searchInput || !resultsContainer || !loader || !themeToggle) {
        console.error('One or more required elements not found');
        return false;
    }
    
    return true;
}

function initializeSearch() {
    if (!initializeElements()) {
        return;
    }
    
    initializeTheme();
    initializeEventListeners();
}

document.addEventListener('DOMContentLoaded', initializeSearch);