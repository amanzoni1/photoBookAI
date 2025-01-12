import React, { useEffect, useRef } from 'react';
import './GradientBackground.css';

function GradientBackground() {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        const colors = [
            // '#75b5ff', // Added: Soft medium blue
            '#90e0ff', // Light blue
            '#ff97c1', // Pink
            '#a960ee'  // Purple
        ];

        function drawGradient() {
            const width = canvas.width;
            const height = canvas.height;

            // Clear canvas
            ctx.clearRect(0, 0, width, height);

            // Draw gradient background
            const gradient = ctx.createLinearGradient(0, 0, width, height * 0.8);
            colors.forEach((color, index) => {
                gradient.addColorStop(index * (1 / (colors.length - 1)), color);
            });

            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, width, height);

            // Draw angled bottom edge
            ctx.beginPath();
            ctx.moveTo(0, height);
            ctx.lineTo(width, height * 0.6); // This creates the angle
            ctx.lineTo(width, height);
            ctx.closePath();
            ctx.fillStyle = '#f0ead6'; // Match your page background color
            ctx.fill();
        }

        function handleResize() {
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            drawGradient();
        }

        window.addEventListener('resize', handleResize);
        handleResize();

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <canvas ref={canvasRef} className="gradient-canvas" />
    );
}

export default GradientBackground;