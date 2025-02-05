// client/src/pages/LandingPage/components/FAQSection.js
import React from "react";
import "./FAQSection.css";

function FAQSection({ id }) {
  const faqs = [
    {
      question: "What kind of photos should I upload?",
      answer:
        "Aim for variety: different angles, expressions, and simple backgrounds. Avoid heavy filters, makeup, or oversized accessories. The more diverse your photos, the more accurate the AI-generated results.",
    },
    {
      question: "How do you handle the photos I upload?",
      answer:
        "We only use the photos to train our AI model. Once training is complete, these original images are securely deleted—immediately after processing or upon your request. Your privacy and your child's safety are our top concerns.",
    },
    {
      question: "Is it safe to upload kids’ photos? Are prompts moderated?",
      answer:
        "Yes. We have strict child-safety protocols in place and automatically block inappropriate or explicit prompts. All uploaded images are stored with top-level security.",
    },
    {
      question: "What happens to the generated AI photos?",
      answer:
        "The AI-generated photos belong to you. You can keep them on our platform as long as you like or delete them anytime if you prefer. We store them securely for quick access and downloads.",
    },
    {
      question: "How many images do I get from each photoshoot?",
      answer:
        "Each themed photoshoot includes 20 unique, high-resolution images. You can select your favorites to download, print, or share.",
    },
    {
      question: "What photoshoot themes are available?",
      answer:
        "We offer a variety of fun scenarios like Superhero, Nature Adventure, Princess, Christmas, Floral Garden, Dream Jobs, School Time, Fairyland, and more. We’re always adding new themes to keep things fresh.",
    },
    {
      question: "How long does it usually take?",
      answer:
        "Most photoshoots finish within a few hours of uploading your child's snapshots. Exact times may vary depending on server load, but same-day results are the norm.",
    },
    {
      question: "Can I use these images for personal or commercial products?",
      answer:
        "Absolutely. Many parents turn them into calendars, photo books, mugs, or social media posts. Your AI portraits come in high resolution, perfect for both digital and print uses.",
    },
    {
      question: "How secure is the payment process?",
      answer:
        "We use Stripe, a trusted payment provider with industry-leading security protocols. Your card details never touch our servers.",
    },
  ];

  return (
    <section id={id} className="faq-section">
      <div className="faq-inner">
        <h2 className="section-title">Frequently Asked Questions</h2>
        <p className="section-subtitle">
          Learn more about our AI-powered photoshoot process, child safety, and
          how you can make the most of your final images.
        </p>

        <div className="faqs-container">
          {faqs.map((item, index) => (
            <div className="faq-item" key={index}>
              <h3 className="faq-question">{item.question}</h3>
              <p className="faq-answer">{item.answer}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default FAQSection;
