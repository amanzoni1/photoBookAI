import React, { useEffect, useRef } from 'react';
import './Background.css';

function Background() {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        const colors = [
            '#90e0ff', // Light blue
            '#ff97c1', // Pink
            '#a960ee', // Purple
            '#90e0ff'
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

            // Draw gradient within the inclined borders
            ctx.beginPath();
            ctx.moveTo(0, height * 0.65); // Top-left inclined
            ctx.lineTo(width, height * 0.35); // Top-right inclined
            ctx.lineTo(width, height * 0.65); // Bottom-right inclined
            ctx.lineTo(0, height * 0.95); // Bottom-left inclined
            ctx.closePath();
            ctx.fill();

            // Fill the remaining area with background color
            ctx.fillStyle = '#ebeef1'; // Match your page background color

            // Fill top area
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.lineTo(width, 0);
            ctx.lineTo(width, height * 0.1);
            ctx.lineTo(0, height * 0.1);
            ctx.closePath();
            ctx.fill();

            // Fill bottom area
            ctx.beginPath();
            ctx.moveTo(0, height * 0.95);
            ctx.lineTo(width, height * 0.65);
            ctx.lineTo(width, height);
            ctx.lineTo(0, height);
            ctx.closePath();
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
        <canvas ref={canvasRef} className="gen-gradient-canvas" />
    );
}

export default Background;